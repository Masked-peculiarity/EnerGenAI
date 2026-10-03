"""Read-only tools; date references are relative to the demo dataset."""
import re
import pandas as pd

def plan_tools(question):
    query = question.lower()
    tools = []
    if any(word in query for word in ["usage","consumption","summary","high","yesterday","today","energy"]):
        tools.append("get_energy_summary")
    if any(word in query for word in ["trend","timeseries","history","over time"]):
        tools.append("get_energy_timeseries")
    if any(word in query for word in ["forecast","predict","next hour","next day"]):
        tools.append("forecast_energy")
    if any(word in query for word in ["anomal","unusual","spike","high","why"]):
        tools.append("detect_anomalies")
    if any(word in query for word in ["peak","highest","high","why"]):
        tools.append("get_peak_usage")
    if any(word in query for word in ["cost","tariff","bill","price"]):
        tools.append("estimate_cost")
    if any(word in query for word in ["carbon","co2","emission"]):
        tools.append("estimate_carbon")
    tools.append("search_energy_knowledge")
    return list(dict.fromkeys(tools))

def resolve_period(question,energy):
    latest = energy.frame.date.iloc[-1].normalize()
    query = question.lower()
    dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b",query)
    if dates:
        return dates[0],(pd.Timestamp(dates[-1])+pd.Timedelta(days=1)).isoformat()
    if "yesterday" in query:
        return (latest-pd.Timedelta(days=1)).isoformat(),latest.isoformat()
    if "today" in query:
        return latest.isoformat(),(latest+pd.Timedelta(days=1)).isoformat()
    return None,None

def execute_tool(name,state,energy,rag):
    start,end = state.get("start"),state.get("end")
    if name=="get_energy_summary":
        return energy.summary(start,end)
    if name=="get_energy_timeseries":
        return energy.timeseries(start,end,limit=48)
    if name=="forecast_energy":
        result = energy.forecast(144 if "day" in state["question"].lower() else 6)
        return {**result,"predictions":result["predictions"][:12],"displayed_steps":min(len(result["predictions"]),12)}
    if name=="detect_anomalies":
        return energy.anomalies(start,end,limit=5)
    if name=="get_peak_usage":
        summary = energy.summary(start,end)
        return {"peak_hour":summary["peak_hour"],"peak_interval":summary["peak_interval"]}
    if name=="estimate_cost":
        summary = energy.summary(start,end,tariff=state.get("tariff"))
        return {"total_kwh":summary["total_appliance_kwh"],"tariff_per_kwh":state.get("tariff"),
                "estimated_cost":summary["estimated_cost"],"basis":summary["cost_basis"]}
    if name=="estimate_carbon":
        summary = energy.summary(start,end,factor=state.get("factor"))
        return {"total_kwh":summary["total_appliance_kwh"],"factor_kg_per_kwh":state.get("factor"),"estimated_carbon_kg":summary["estimated_carbon_kg"]}
    if name=="search_energy_knowledge":
        return rag.search(state["question"],state.get("username"))
    raise ValueError("Unknown tool")
