"""Reproducible EDA summaries and figures for product decisions."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ml.data.load_data import load_data

def analyze(output=None):
    frame,validation = load_data()
    output = Path(output or Path(__file__).resolve().parents[1]/"reports/eda")
    output.mkdir(parents=True,exist_ok=True)
    summary = {"validation":validation,"target_distribution":frame.Appliances.describe().to_dict(),
        "hourly_mean_interval_wh":frame.groupby(frame.date.dt.hour).Appliances.mean().to_dict(),
        "weekday_mean_interval_wh":frame.groupby(frame.date.dt.dayofweek).Appliances.mean().to_dict(),
        "weekday_vs_weekend_wh":frame.groupby(frame.date.dt.dayofweek>=5).Appliances.mean().rename(index={False:"weekday",True:"weekend"}).to_dict(),
        "monthly_mean_interval_wh":frame.groupby(frame.date.dt.strftime("%Y-%m")).Appliances.mean().to_dict(),
        "correlations":frame.drop(columns="date").corr()["Appliances"].to_dict(),
        "peak_intervals":[{"timestamp":row.date.isoformat(),"appliances_wh":float(row.Appliances)} for _,row in frame.nlargest(10,"Appliances").iterrows()]}
    (output/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    def save(name,title,xlabel,ylabel):
        plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.tight_layout(); plt.savefig(output/f"{name}.png",dpi=120); plt.close()
    plt.figure(figsize=(12,4)); plt.plot(frame.date,frame.Appliances,linewidth=.4)
    save("timeseries","UCI appliance energy over time","Dataset local timestamp (2016)","Appliance energy (Wh / 10 min)")
    for grouping,name,label in [(frame.date.dt.hour,"hourly_profile","Hour"),(frame.date.dt.dayofweek,"weekday_profile","Day (Monday=0)"),(frame.date.dt.strftime("%Y-%m"),"monthly_profile","Month")]:
        plt.figure(figsize=(8,4)); frame.groupby(grouping).Appliances.mean().plot.bar()
        save(name,"Mean energy per ten-minute interval",label,"Mean appliance energy (Wh / 10 min)")
    for values,name,label in [(frame.Appliances,"distribution","Appliance energy (Wh / 10 min)"),(np.log1p(frame.Appliances),"log_distribution","log(1 + appliance Wh)")]:
        plt.figure(figsize=(7,4)); plt.hist(values,bins=50); save(name,"Target distribution",label,"Intervals")
    sample = frame.sample(min(5000,len(frame)),random_state=42)
    for column in ["lights","T1","RH_1","T_out","RH_out"]:
        plt.figure(figsize=(7,4)); plt.scatter(sample[column],sample.Appliances,s=3,alpha=.2)
        save(column,"Association with appliance energy; not causation",column,"Appliance energy (Wh / 10 min)")
    corr = frame.drop(columns="date").corr()
    plt.figure(figsize=(11,9)); plt.imshow(corr,vmin=-1,vmax=1,cmap="coolwarm"); plt.colorbar(label="Pearson correlation")
    plt.xticks(range(len(corr)),corr.columns,rotation=90,fontsize=7); plt.yticks(range(len(corr)),corr.columns,fontsize=7)
    save("correlations","Indoor and outdoor correlations","Variable","Variable")
    for aggregation,label in [("mean","Wh / 10 min"),("var","Wh squared")]:
        plt.figure(figsize=(12,4)); values = getattr(frame.Appliances.rolling(144),aggregation)(); plt.plot(frame.date,values)
        save("rolling_"+aggregation,"24-hour rolling "+aggregation,"Dataset local timestamp",label)
    print(f"EDA complete: {len(frame)} observations in {output}")
    return summary

if __name__=="__main__":
    analyze()
