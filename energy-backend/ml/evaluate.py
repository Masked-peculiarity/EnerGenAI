import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def metrics(actual, predicted):
    actual, predicted = np.asarray(actual), np.maximum(np.asarray(predicted), 0)
    denominator = np.abs(actual) + np.abs(predicted)
    smape = np.divide(2*np.abs(actual-predicted), denominator, out=np.zeros_like(denominator, dtype=float), where=denominator!=0).mean()*100
    return {"mae_wh": float(mean_absolute_error(actual,predicted)), "rmse_wh": float(np.sqrt(mean_squared_error(actual,predicted))),
            "r2": float(r2_score(actual,predicted)), "smape_percent": float(smape)}
