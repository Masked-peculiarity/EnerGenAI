"""Forecast features use strictly earlier measurements."""
import numpy as np
import pandas as pd
from ml.data.load_data import SENSOR_COLUMNS, WEATHER_COLUMNS

LAGS = (1, 3, 6, 12, 18, 36, 144)
MEAN_WINDOWS = (3, 6, 12, 36, 144)
STD_WINDOWS = (6, 36, 144)
PAST_COLUMNS = ["lights", *SENSOR_COLUMNS, *WEATHER_COLUMNS]
WARMUP = 144

def calendar_features(dates):
    dates = pd.DatetimeIndex(dates)
    hour = dates.hour + dates.minute / 60
    return pd.DataFrame({"hour": dates.hour, "minute": dates.minute, "day_of_week": dates.dayofweek,
        "day_of_month": dates.day, "month": dates.month, "is_weekend": (dates.dayofweek >= 5).astype(int),
        "hour_sin": np.sin(2*np.pi*hour/24), "hour_cos": np.cos(2*np.pi*hour/24),
        "minute_sin": np.sin(2*np.pi*dates.minute/60), "minute_cos": np.cos(2*np.pi*dates.minute/60),
        "dow_sin": np.sin(2*np.pi*dates.dayofweek/7), "dow_cos": np.cos(2*np.pi*dates.dayofweek/7)})

def build_features(frame):
    result = calendar_features(frame.date)
    target = frame.Appliances
    for lag in LAGS:
        result[f"lag_{lag}"] = target.shift(lag)
    past = target.shift(1)
    for window in MEAN_WINDOWS:
        result[f"rolling_mean_{window}"] = past.rolling(window).mean()
    for window in STD_WINDOWS:
        result[f"rolling_std_{window}"] = past.rolling(window).std(ddof=0)
    result["recent_change"] = target.shift(1) - target.shift(3)
    for name in PAST_COLUMNS:
        result[f"{name}_prev"] = frame[name].shift(1)
    return result.iloc[WARMUP:].reset_index(drop=True).astype("float32")

def next_features(timestamp, history_values, last_sensors, feature_names):
    if len(history_values) < WARMUP:
        raise ValueError("At least 24 hours of observations are required")
    result = calendar_features([timestamp])
    values = np.asarray(history_values, dtype=float)
    for lag in LAGS:
        result[f"lag_{lag}"] = values[-lag]
    for window in MEAN_WINDOWS:
        result[f"rolling_mean_{window}"] = values[-window:].mean()
    for window in STD_WINDOWS:
        result[f"rolling_std_{window}"] = values[-window:].std(ddof=0)
    result["recent_change"] = values[-1] - values[-3]
    for name in PAST_COLUMNS:
        result[f"{name}_prev"] = float(last_sensors[name])
    return result.reindex(columns=feature_names).astype("float32")

def recursive_forecast(model, history, horizon, feature_names, model_name):
    values = history.Appliances.to_list()
    sensors = history.iloc[-1]
    origin = history.date.iloc[-1]
    output = []
    for step in range(1, horizon + 1):
        timestamp = origin + pd.Timedelta(minutes=10*step)
        row = next_features(timestamp, values, sensors, feature_names)
        prediction = values[-1] if model_name == "persistence" else float(model.predict(row)[0])
        prediction = max(0.0, prediction)
        values.append(prediction)
        output.append({"timestamp": timestamp.isoformat(), "appliances_wh": round(prediction, 3)})
    return output
