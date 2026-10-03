"""Local training and chronological evaluation; never called at API startup."""
import argparse
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from ml.data.load_data import DEFAULT_DATASET, load_data
from ml.features import WARMUP, build_features, recursive_forecast
from ml.evaluate import metrics
from ml.train_anomaly import fit_anomaly

MODELS = Path(__file__).resolve().parents[1] / "models"

def train(dataset=DEFAULT_DATASET, output=MODELS):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frame, validation = load_data(dataset)
    X = build_features(frame)
    y = frame.Appliances.iloc[WARMUP:].to_numpy()
    n = len(X)
    train_end, val_end = int(n*.70), int(n*.85)
    slices = {"train":slice(0,train_end), "validation":slice(train_end,val_end), "test":slice(val_end,n)}
    candidates = {
        "persistence": None,
        "ridge": make_pipeline(StandardScaler(),Ridge(alpha=100)),
        "random_forest": RandomForestRegressor(n_estimators=100,max_depth=12,min_samples_leaf=5,max_features=.8,random_state=42,n_jobs=2),
        "xgboost": XGBRegressor(n_estimators=350,max_depth=4,learning_rate=.04,subsample=.85,colsample_bytree=.85,
                                reg_lambda=10,min_child_weight=15,objective="reg:squarederror",tree_method="hist",n_jobs=2,random_state=42),
        "xgboost_absolute": XGBRegressor(n_estimators=400,max_depth=3,learning_rate=.025,subsample=.9,colsample_bytree=.9,
                                reg_lambda=10,min_child_weight=20,objective="reg:absoluteerror",tree_method="hist",n_jobs=2,random_state=42),
    }
    comparison, predictions = {}, {}
    for name, model in candidates.items():
        started = time.perf_counter()
        if model is not None:
            model.fit(X.iloc[:train_end],y[:train_end])
            pred = np.maximum(model.predict(X),0)
        else:
            pred = X.lag_1.to_numpy()
        predictions[name] = pred
        comparison[name] = {split:metrics(y[section],pred[section]) for split,section in slices.items() if split!="train"}
        comparison[name]["fit_seconds"] = round(time.perf_counter()-started,3)
        print(f"{name}: validation MAE {comparison[name]['validation']['mae_wh']:.3f} Wh",flush=True)
    selected = min(comparison,key=lambda name:comparison[name]["validation"]["mae_wh"])
    model, pred = candidates[selected], predictions[selected]
    joblib.dump({"model":model,"name":selected,"feature_names":list(X.columns)},output/"forecast_model.pkl",compress=3)
    detector, iso_features, threshold = fit_anomaly(frame,train_end+WARMUP,y[train_end:val_end]-pred[train_end:val_end])
    joblib.dump(detector,output/"anomaly_model.pkl",compress=3)
    scores = -detector.decision_function(iso_features.iloc[WARMUP:])
    labels = np.full(n,"train",dtype=object)
    labels[train_end:val_end], labels[val_end:] = "validation", "test"
    residual = y-pred
    pd.DataFrame({"timestamp":frame.date.iloc[WARMUP:].to_numpy(),"actual_wh":y,"predicted_wh":pred,"residual":residual,
        "anomaly_score":scores,"residual_flag":np.abs(residual)>threshold,"isolation_flag":scores>0,
        "is_anomaly":(np.abs(residual)>threshold)|(scores>0),"split":labels}).to_csv(output/"evaluation.csv",index=False)
    multi_step = {}
    for horizon in [6,144]:
        actual, forecast, naive = [], [], []
        origins = np.linspace(val_end+WARMUP-1,len(frame)-horizon-1,12,dtype=int)
        for origin in origins:
            past = frame.iloc[:origin+1]
            future = recursive_forecast(model,past,horizon,list(X.columns),selected)
            actual.extend(frame.Appliances.iloc[origin+1:origin+1+horizon].tolist())
            forecast.extend(row["appliances_wh"] for row in future)
            naive.extend([float(past.Appliances.iloc[-1])]*horizon)
        multi_step[str(horizon)] = {"origins":12,"horizon_minutes":horizon*10,"selected_model":metrics(actual,forecast),"persistence":metrics(actual,naive)}
    report = {"dataset":validation,"selected_model":selected,"selection_rule":"lowest validation MAE, including persistence",
        "split_strategy":"chronological 70/15/15 after 144-row warmup","warmup_rows":WARMUP,
        "splits":{name:{"rows":len(X.iloc[section]),"start":frame.date.iloc[WARMUP+section.start].isoformat(),
                        "end":frame.date.iloc[WARMUP+section.stop-1].isoformat()} for name,section in slices.items()},
        "comparison":comparison,"recursive_test":multi_step,"residual_threshold_wh":threshold,
        "evaluation_policy":"one-step uses observed past values; recursive multi-step uses only history at origin",
        "versions":{"sklearn":sklearn.__version__,"xgboost":xgboost.__version__}}
    (output/"metrics.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (output/"feature_schema.json").write_text(json.dumps({"features":list(X.columns),"target":"Appliances","unit":"Wh"},indent=2),encoding="utf-8")
    (output/"preprocessing_config.json").write_text(json.dumps({"interval_minutes":10,"warmup":WARMUP,"excluded":["rv1","rv2"],
        "sensors":"shifted one interval; persisted at origin during recursion","dataset_sha256":validation["sha256"]},indent=2),encoding="utf-8")
    print(f"Selected {selected}; test MAE {comparison[selected]['test']['mae_wh']:.3f} Wh",flush=True)
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset",default=str(DEFAULT_DATASET))
    parser.add_argument("--output",default=str(MODELS))
    args = parser.parse_args()
    train(args.dataset,args.output)
