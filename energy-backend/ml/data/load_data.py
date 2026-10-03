"""Strict ingestion of UCI Appliances Energy Prediction data."""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "energydata_complete.csv"
SENSOR_COLUMNS = [f"T{i}" for i in range(1, 10)] + [f"RH_{i}" for i in range(1, 10)]
WEATHER_COLUMNS = ["T_out", "Press_mm_hg", "RH_out", "Windspeed", "Visibility", "Tdewpoint"]
REQUIRED_COLUMNS = ["date", "Appliances", "lights", *SENSOR_COLUMNS, *WEATHER_COLUMNS, "rv1", "rv2"]

def load_data(path=DEFAULT_DATASET):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Energy dataset not found at {path}. Restore the original "
            "energydata_complete.csv in the repository root (see data/README.md), "
            "or set DATASET_PATH to its existing location and restart the backend."
        )
    frame = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(REQUIRED_COLUMNS))
    if missing or extra:
        raise ValueError(f"Dataset schema mismatch: missing={missing}, unexpected={extra}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError("Missing or duplicate timestamps")
    frame = frame.sort_values("date").reset_index(drop=True)
    if len(frame) < 1000:
        raise ValueError("At least 1,000 ten-minute observations are required")
    for name in REQUIRED_COLUMNS[1:]:
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    if not np.isfinite(frame[REQUIRED_COLUMNS[1:]].to_numpy()).all():
        raise ValueError("Missing or non-finite measurements")
    if not frame["date"].diff().iloc[1:].eq(pd.Timedelta(minutes=10)).all():
        raise ValueError("Dataset must have uninterrupted ten-minute intervals")
    for name in [*SENSOR_COLUMNS[:9], "T_out", "Tdewpoint"]:
        if not frame[name].between(-80, 80).all():
            raise ValueError(f"Impossible temperature in {name}")
    for name in [*SENSOR_COLUMNS[9:], "RH_out"]:
        if not frame[name].between(0, 100).all():
            raise ValueError(f"Impossible humidity in {name}")
    for name in ["Appliances", "lights", "Windspeed", "Visibility"]:
        if (frame[name] < 0).any():
            raise ValueError(f"Negative measurement in {name}")
    frame = frame.drop(columns=["rv1", "rv2"])
    report = {"rows": len(frame), "start": frame.date.iloc[0].isoformat(), "end": frame.date.iloc[-1].isoformat(),
              "interval_minutes": 10, "target": "Appliances", "unit": "Wh per ten-minute interval",
              "missing_values": 0, "duplicate_timestamps": 0, "irregular_intervals": 0,
              "excluded_columns": ["rv1", "rv2"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return frame, report
