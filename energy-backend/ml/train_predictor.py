"""Train conditions and home-profile regressors; never concatenate incompatible targets."""
import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor
from ml.data.load_data import load_data, DEFAULT_DATASET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "energy-backend/models/predictor"
RECS = ROOT / "data/recs2020_predictor.csv"
RECS_COLUMNS = ["DOEID","TOTSQFT_EN","NHSLDMEM","HDD65","CDD65","TYPEHUQ","FUELHEAT","AIRCOND","KWH","NWEIGHT"]
HOME_MAP = {"TOTSQFT_EN":"floor_area_sqft","NHSLDMEM":"occupants","HDD65":"heating_degree_days",
            "CDD65":"cooling_degree_days","TYPEHUQ":"home_type","FUELHEAT":"heating_fuel","AIRCOND":"air_conditioning"}

def conditions(frame):
    dates = pd.to_datetime(frame.date)
    return pd.DataFrame({
        "temperature_c": frame[[f"T{i}" for i in range(1,10)]].mean(axis=1),
        "humidity_percent": frame[[f"RH_{i}" for i in range(1,10)]].mean(axis=1),
        "lighting_wh": frame.lights, "outdoor_temperature_c": frame.T_out,
        "hour": dates.dt.hour + dates.dt.minute/60,
        "day_of_week": dates.dt.dayofweek, "month": dates.dt.month})

def scores(y, prediction, weights=None):
    prediction = np.maximum(prediction,0)
    return {"mae":float(mean_absolute_error(y,prediction,sample_weight=weights)),
            "rmse":float(np.sqrt(mean_squared_error(y,prediction,sample_weight=weights))),
            "r2":float(r2_score(y,prediction,sample_weight=weights))}

def fit_mode(mode, X, y, weights, metadata, categorical=()):
    n = len(X)
    ids = np.arange(n)
    if mode == "conditions":
        sections = np.split(ids,[int(n*.60),int(n*.75),int(n*.85)])
        split_policy = "chronological 60/15/10/15: train/selection/calibration/test"
    else:
        train, rest = train_test_split(ids,test_size=.4,random_state=42)
        selection, rest = train_test_split(rest,test_size=.625,random_state=43)
        calibration, test = train_test_split(rest,test_size=.6,random_state=44)
        sections = [train,selection,calibration,test]
        split_policy = "household-random 60/15/10/15, fixed seeds 42/43/44; survey-weighted fit/evaluation"
    train, select, cal, test = sections
    numeric = [name for name in X if name not in categorical]
    transform = ColumnTransformer([("numeric",StandardScaler(),numeric),
        ("categorical",OneHotEncoder(handle_unknown="ignore",sparse_output=False),list(categorical))])
    candidates = {"mean_baseline":DummyRegressor(strategy="mean"),"median_baseline":DummyRegressor(strategy="median"),"ridge":Ridge(alpha=100),
        "extra_trees":ExtraTreesRegressor(n_estimators=120,min_samples_leaf=10,max_features=.9,n_jobs=2,random_state=42),
        "xgboost":XGBRegressor(n_estimators=300,max_depth=4,learning_rate=.04,subsample=.85,colsample_bytree=.9,
            reg_lambda=15,min_child_weight=20,tree_method="hist",n_jobs=2,random_state=42),
        "xgboost_absolute":XGBRegressor(n_estimators=300,max_depth=3,learning_rate=.025,subsample=.9,colsample_bytree=.9,
            reg_lambda=15,min_child_weight=20,objective="reg:absoluteerror",tree_method="hist",n_jobs=2,random_state=42)}
    models, comparison = {}, {}
    for name, estimator in candidates.items():
        model = Pipeline([("preprocess",transform),("model",estimator)])
        # Each fitted pipeline needs an independent preprocessor.
        from sklearn.base import clone
        model = clone(model)
        model.fit(X.iloc[train],y[train],model__sample_weight=weights[train])
        comparison[name] = {"selection":scores(y[select],model.predict(X.iloc[select]),weights[select])}
        models[name] = model
    name = min(comparison,key=lambda key:comparison[key]["selection"]["mae"])
    model = models[name]
    residuals = np.abs(y[cal]-np.maximum(model.predict(X.iloc[cal]),0))
    # Unweighted split-conformal calibration, kept separate from model selection.
    quantile = min(1, np.ceil((len(cal)+1)*.8)/len(cal))
    radius = float(np.quantile(residuals,quantile,method="higher"))
    for key, candidate in models.items():
        comparison[key]["test"] = scores(y[test],candidate.predict(X.iloc[test]),weights[test])
    pred = np.maximum(model.predict(X.iloc[test]),0)
    bounds = {key:{"min":float(X.iloc[train][key].min()),"max":float(X.iloc[train][key].max()),
                  "default":float(X.iloc[train][key].median())} for key in numeric}
    choices = {key:sorted(int(v) for v in X.iloc[train][key].unique()) for key in categorical}
    report = {**metadata,"mode":mode,"selected_model":name,"selection_rule":"lowest selection MAE",
        "features":list(X.columns),"ranges":bounds,"choices":choices,"split_policy":split_policy,
        "split_rows":dict(zip(["train","selection","calibration","test"],map(len,sections))),
        "comparison":comparison,"metrics":comparison[name]["test"],"interval":{
            "nominal_coverage":.8,"radius":radius,"test_coverage":float(np.mean(np.abs(y[test]-pred)<=radius)),
            "method":"unweighted absolute residual split-conformal; no guarantee under domain/time shift"},
        "target_in_features":False,
        "examples":[{"inputs":{key:float(X.iloc[index][key]) if key in numeric else int(X.iloc[index][key]) for key in X},
                     "actual":float(y[index])} for index in test[:3]]}
    OUT.mkdir(parents=True,exist_ok=True)
    joblib.dump({"model":model,"report":report},OUT/f"{mode}.pkl",compress=3)
    (OUT/f"{mode}.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(mode,name,report["metrics"],flush=True)
    return report

def train(recs_source=None):
    if recs_source:
        source = pd.read_csv(recs_source,usecols=RECS_COLUMNS)
        RECS.parent.mkdir(parents=True,exist_ok=True)
        source.to_csv(RECS,index=False)
    frame, provenance = load_data(DEFAULT_DATASET)
    fit_mode("conditions",conditions(frame),frame.Appliances.to_numpy(),np.ones(len(frame)),{
        "source":"UCI Appliances Energy Prediction; one Belgian household, 2016",
        "source_url":"https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction",
        "dataset_sha256":provenance["sha256"],"rows":len(frame),"unit":"Wh per 10-minute interval",
        "target":"Appliances","warning":"Experimental conditional estimate, not a forecast or causal saving. Same-interval lighting/sensors must be supplied; not validated for other homes."})
    raw = pd.read_csv(RECS)
    if raw.DOEID.duplicated().any():
        raise ValueError("RECS household IDs must be unique")
    required = list(HOME_MAP)+["KWH","NWEIGHT"]
    valid = np.isfinite(raw[required]).all(axis=1)
    valid &= (raw.TOTSQFT_EN>0)&(raw.NHSLDMEM>0)&(raw.HDD65>=0)&(raw.CDD65>=0)&(raw.KWH>=0)&(raw.NWEIGHT>0)
    valid &= raw.TYPEHUQ.isin([1,2,3,4,5])&raw.FUELHEAT.isin([1,2,3,5,7,99,-2])&raw.AIRCOND.isin([0,1])
    rows = raw.loc[valid].reset_index(drop=True)
    fit_mode("home",rows[list(HOME_MAP)].rename(columns=HOME_MAP),rows.KWH.to_numpy(),
        rows.NWEIGHT.to_numpy()/rows.NWEIGHT.mean(),{
            "source":"U.S. EIA 2020 Residential Energy Consumption Survey, public v7",
            "source_url":"https://www.eia.gov/consumption/residential/data/2020/index.php?view=microdata",
            "dataset_sha256":hashlib.sha256(RECS.read_bytes()).hexdigest(),"rows":len(rows),
            "excluded_rows":len(raw)-len(rows),"unit":"kWh per year","target":"KWH",
            "warning":"U.S. 2020 household-profile estimate, including self-generated solar electricity. Not validated for India or a specific home; not a bill or hourly forecast. HVAC fields describe heating fuel and AC use, not real-time On/Off. Occupants are top-coded at 7 (7 or more)."},
        categorical=("home_type","heating_fuel","air_conditioning"))

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recs-source",help="Official full public v7 CSV; creates the documented feature-only subset")
    train(parser.parse_args().recs_source)
