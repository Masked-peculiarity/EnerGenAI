import numpy as np
from sklearn.ensemble import IsolationForest
from ml.features import calendar_features

def anomaly_features(frame):
    output = calendar_features(frame.date)
    for name in ["Appliances", "lights", "T1", "RH_1", "T_out", "RH_out"]:
        output[name] = frame[name].to_numpy()
    output["previous_hour_mean"] = frame.Appliances.shift(1).rolling(6,min_periods=1).mean().fillna(0).to_numpy()
    return output.astype("float32")

def fit_anomaly(frame, train_end, validation_residuals):
    features = anomaly_features(frame)
    detector = IsolationForest(n_estimators=120, contamination=.02, random_state=42, n_jobs=2)
    detector.fit(features.iloc[:train_end])
    absolute = np.abs(validation_residuals)
    median = np.median(absolute)
    mad = np.median(np.abs(absolute-median))
    threshold = float(max(np.quantile(absolute,.99), median+6*1.4826*mad))
    return detector, features, threshold
