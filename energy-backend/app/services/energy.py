import json
from functools import lru_cache
import joblib
import pandas as pd
from app.config import DATASET_PATH, MODEL_DIR
from ml.data.load_data import load_data
from ml.features import recursive_forecast

class EnergyService:
    def __init__(self,dataset=DATASET_PATH,models=MODEL_DIR):
        self.frame,self.dataset = load_data(dataset)
        self.metrics = json.loads((models/"metrics.json").read_text(encoding="utf-8"))
        if self.dataset["sha256"]!=self.metrics["dataset"]["sha256"]:
            raise RuntimeError("Dataset differs from trained model; run python -m ml.train_forecast")
        self.artifact = joblib.load(models/"forecast_model.pkl")
        self.anomaly_model = joblib.load(models/"anomaly_model.pkl")
        self.evaluation = pd.read_csv(models/"evaluation.csv",parse_dates=["timestamp"])
        self.evaluation = self.evaluation[self.evaluation.split!="train"].reset_index(drop=True)

    def period(self,start=None,end=None):
        last = self.frame.date.iloc[-1]
        lower = pd.Timestamp(start) if start else last.normalize()-pd.Timedelta(days=6)
        upper = pd.Timestamp(end) if end else last+pd.Timedelta(minutes=10)
        if pd.isna(lower) or pd.isna(upper):
            raise ValueError("Use valid dataset-local dates")
        if lower.tzinfo or upper.tzinfo:
            raise ValueError("Dataset uses unspecified local timezone; use timestamps without UTC offsets")
        if lower>=upper:
            raise ValueError("start must precede end; end is exclusive")
        return lower,upper

    def select(self,start=None,end=None):
        lower,upper = self.period(start,end)
        rows = self.frame[(self.frame.date>=lower)&(self.frame.date<upper)]
        if rows.empty:
            raise ValueError("No UCI observations in that period; use dates within the dataset range")
        return rows

    def summary(self,start=None,end=None,tariff=None,factor=None):
        rows = self.select(start,end)
        hourly = rows.groupby(rows.date.dt.floor("h")).Appliances.agg(["sum","count"])
        daily = rows.groupby(rows.date.dt.normalize()).Appliances.agg(["sum","count"])
        complete_hours,complete_days = hourly[hourly["count"]==6],daily[daily["count"]==144]
        peak_row,peak_hour = rows.loc[rows.Appliances.idxmax()],hourly["sum"].idxmax()
        latest_day = self.frame.date.iloc[-1].normalize()
        today = self.frame[self.frame.date.dt.normalize()==latest_day]
        total = float(rows.Appliances.sum()/1000)
        anomaly,future = self.anomalies(start,end,limit=1),self.forecast(6)
        return {"source":"UCI demonstration household, Belgium, 2016","period_start":rows.date.iloc[0].isoformat(),
            "period_end":rows.date.iloc[-1].isoformat(),"observations":len(rows),"latest_appliances_wh":float(rows.Appliances.iloc[-1]),
            "total_appliance_kwh":total,"lighting_kwh":float(rows.lights.sum()/1000),
            "average_hourly_wh":float(complete_hours["sum"].mean()) if len(complete_hours) else None,
            "daily_average_kwh":float(complete_days["sum"].mean()/1000) if len(complete_days) else None,
            "latest_recorded_day":latest_day.date().isoformat(),"latest_day_kwh":float(today.Appliances.sum()/1000),
            "latest_day_intervals":len(today),"peak_interval":{"timestamp":peak_row.date.isoformat(),"appliances_wh":float(peak_row.Appliances)},
            "peak_hour":{"timestamp":peak_hour.isoformat(),"appliances_wh":float(hourly.loc[peak_hour,"sum"]),"intervals":int(hourly.loc[peak_hour,"count"])},
            "unusual_intervals":anomaly["total"] if anomaly["evaluated_intervals"] else None,"predicted_next_hour_kwh":future["total_kwh"],
            "estimated_cost":total*tariff if tariff is not None else None,"tariff_per_kwh":tariff,
            "estimated_carbon_kg":total*factor if factor is not None else None,"emission_factor_kg_per_kwh":factor,
            "cost_basis":"appliance channel only; excludes lighting, fixed fees and taxes","model":self.artifact["name"]}

    def timeseries(self,start=None,end=None,resolution="hour",limit=1000):
        rows = self.select(start,end)
        rules = {"10min":"10min","hour":"h","day":"D"}
        if resolution not in rules:
            raise ValueError("resolution must be 10min, hour, or day")
        grouped = rows.set_index("date")[["Appliances","lights"]].resample(rules[resolution]).sum()
        output = [{"timestamp":date.isoformat(),"appliances_wh":float(row.Appliances),"lights_wh":float(row.lights)} for date,row in grouped.iterrows()]
        return {"rows":output[:limit],"total_points":len(output),"truncated":len(output)>limit,"resolution":resolution,"unit":"Wh per selected interval"}

    @lru_cache(maxsize=32)
    def forecast(self,horizon=6,origin=None):
        if not 1<=horizon<=144:
            raise ValueError("horizon_steps must be between 1 and 144")
        past = self.frame
        if origin:
            timestamp = pd.Timestamp(origin)
            if timestamp.tzinfo:
                raise ValueError("Use a dataset-local origin without timezone offset")
            if timestamp not in set(self.frame.date):
                raise ValueError("origin must match a measured dataset timestamp")
            past = self.frame[self.frame.date<=timestamp]
        if len(past)<144:
            raise ValueError("Forecast origin requires 24 hours of prior observations")
        predictions = recursive_forecast(self.artifact["model"],past,horizon,self.artifact["feature_names"],self.artifact["name"])
        observed = self.frame.set_index("date").Appliances
        for row in predictions:
            timestamp = pd.Timestamp(row["timestamp"])
            row["actual_wh"] = float(observed.loc[timestamp]) if timestamp in observed.index else None
        return {"origin":past.date.iloc[-1].isoformat(),"horizon_minutes":horizon*10,"predictions":predictions,
            "total_kwh":sum(row["appliances_wh"] for row in predictions)/1000,"model":self.artifact["name"],
            "unit":"Wh per ten-minute interval","method":"recursive; future environmental values held at last observed values",
            "source":"UCI demonstration household"}

    def anomalies(self,start=None,end=None,limit=200,flagged_only=True):
        lower,upper = self.period(start,end)
        rows = self.evaluation[(self.evaluation.timestamp>=lower)&(self.evaluation.timestamp<upper)]
        evaluated_intervals = len(rows)
        if flagged_only:
            rows = rows[rows.is_anomaly]
        output = [{"timestamp":row.timestamp.isoformat(),"actual_wh":float(row.actual_wh),"predicted_wh":float(row.predicted_wh),
            "residual":float(row.residual),"anomaly_score":float(row.anomaly_score),"is_anomaly":bool(row.is_anomaly),
            "residual_flag":bool(row.residual_flag),"isolation_flag":bool(row.isolation_flag),"split":row.split}
            for _,row in rows.iloc[:limit].iterrows()]
        return {"rows":output,"total":len(rows),"evaluated_intervals":evaluated_intervals,"truncated":len(rows)>limit,"residual_threshold_wh":self.metrics["residual_threshold_wh"],
            "meaning":"Unusual consumption, not fault diagnosis; only validation/test intervals are scored"}

    def backtest(self,limit=288):
        rows = self.evaluation[self.evaluation.split=="test"].tail(limit)
        return {"rows":[{"timestamp":row.timestamp.isoformat(),"actual_wh":float(row.actual_wh),"predicted_wh":float(row.predicted_wh)} for _,row in rows.iterrows()],
            "metrics":self.metrics,"evaluation":"ten-minute one-step rolling origin with observed past values"}
