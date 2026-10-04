"""Manual-input regressors with separate targets and provenance."""
import hashlib
from functools import lru_cache
import joblib
import pandas as pd
from app.config import MODEL_DIR, ROOT, DATASET_PATH

@lru_cache(maxsize=2)
def artifact(mode):
    path = MODEL_DIR/"predictor"/f"{mode}.pkl"
    if not path.is_file():
        raise FileNotFoundError("Predictor models are missing. From energy-backend run python -m ml.train_predictor.")
    bundle = joblib.load(path)
    dataset = DATASET_PATH if mode=="conditions" else ROOT/"data/recs2020_predictor.csv"
    if not dataset.is_file() or hashlib.sha256(dataset.read_bytes()).hexdigest()!=bundle["report"]["dataset_sha256"]:
        raise ValueError("Predictor dataset missing or changed; restore data or retrain with python -m ml.train_predictor.")
    return bundle

def predict(mode, values):
    bundle = artifact(mode)
    report = bundle["report"]
    warnings = [report["warning"]]
    for key, limits in report["ranges"].items():
        if values[key]<limits["min"] or values[key]>limits["max"]:
            warnings.append(f"{key} is outside the training range ({limits['min']:.2f} to {limits['max']:.2f}); estimate may be unreliable.")
    for key, choices in report["choices"].items():
        if values[key] not in choices:
            raise ValueError(f"{key} is not supported by this model")
    row = pd.DataFrame([values],columns=report["features"])
    estimate = max(0,float(bundle["model"].predict(row)[0]))
    radius = report["interval"]["radius"]
    return {"mode":mode,"estimate":round(estimate,3),"unit":report["unit"],
        "interval":{"lower":round(max(0,estimate-radius),3),"upper":round(estimate+radius,3),
                    **report["interval"]},"metrics":report["metrics"],"model":report["selected_model"],
        "source":report["source"],"warnings":warnings,
        "monthly_average_kwh":round(estimate/12,3) if mode=="home" else None}
