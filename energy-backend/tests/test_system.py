from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.storage import Store
from app.services.energy import EnergyService
from app.services.llm import Generator
from app.services.documents import analyze_bill
from ml.features import build_features, next_features, PAST_COLUMNS
from ml.data.load_data import load_data

@pytest.fixture(scope="session")
def service():
    return EnergyService()

@pytest.fixture
def client(tmp_path,service):
    generator=Generator()
    generator.key=""
    with TestClient(create_app(Store(tmp_path/"accounts.sqlite3"),service,generator)) as client:
        yield client

def account(client,email):
    body={"email":email,"password":"StrongPassword123"}
    assert client.post("/api/auth/signup",json=body).status_code==201
    result=client.post("/api/auth/login",json=body)
    assert result.status_code==200
    return {"Authorization":"Bearer "+result.json()["token"]}

def test_health(client):
    result=client.get("/api/health")
    assert result.status_code==200
    assert result.json()["dataset"]["rows"]==19735
    assert result.json()["artifacts_loaded"]

@pytest.mark.parametrize("steps",[1,6,144])
def test_forecast(client,steps):
    result=client.post("/api/forecast",json={"horizon_steps":steps})
    assert result.status_code==200,result.text
    data=result.json()
    assert len(data["predictions"])==steps
    assert all(row["appliances_wh"]>=0 and row["actual_wh"] is None for row in data["predictions"])
    assert data["total_kwh"]==pytest.approx(sum(row["appliances_wh"] for row in data["predictions"])/1000)

@pytest.mark.parametrize("steps",[0,145,1.5,"six"])
def test_forecast_rejects_invalid(client,steps):
    assert client.post("/api/forecast",json={"horizon_steps":steps}).status_code==422

def test_retired_schema_and_bad_dates(client):
    assert client.post("/predict",json={}).status_code==410
    assert client.get("/api/analytics/summary?start=not-a-date").status_code==400
    assert client.get("/api/analytics/summary?start=2026-01-01").status_code==400

def test_units_and_partial_day(service):
    data=service.summary("2016-05-27","2016-05-28",tariff=8,factor=.4)
    measured=service.select("2016-05-27","2016-05-28")
    assert data["total_appliance_kwh"]==pytest.approx(measured.Appliances.sum()/1000)
    assert data["estimated_cost"]==pytest.approx(data["total_appliance_kwh"]*8)
    assert data["estimated_carbon_kg"]==pytest.approx(data["total_appliance_kwh"]*.4)
    assert data["daily_average_kwh"] is None
    assert data["latest_day_intervals"]==109
    assert service.summary()["estimated_cost"] is None

def test_anomaly_coverage(service):
    result=service.anomalies("2016-01-13","2016-01-14")
    assert result["evaluated_intervals"]==0
    assert service.summary("2016-01-13","2016-01-14")["unusual_intervals"] is None
    result=service.anomalies(flagged_only=False)
    assert result["evaluated_intervals"]>0
    for row in result["rows"]:
        assert row["is_anomaly"]==(row["residual_flag"] or row["isolation_flag"])

def test_features_are_strictly_past(service):
    original=service.frame.iloc[:400].copy()
    changed=original.copy()
    changed.loc[200:,["Appliances",*PAST_COLUMNS]]=999
    pd.testing.assert_series_equal(build_features(original).iloc[200-144],build_features(changed).iloc[200-144])
    expected=build_features(original).iloc[200-144]
    online=next_features(original.date.iloc[200],original.Appliances.iloc[:200].tolist(),original.iloc[199],list(expected.index)).iloc[0]
    pd.testing.assert_series_equal(expected,online,check_names=False)

def test_forecast_uses_only_origin_history(service):
    origin=service.frame.date.iloc[18000].isoformat()
    first=service.forecast(6,origin)
    changed=service.frame.copy()
    service.forecast.cache_clear()
    try:
        service.frame.loc[18001:,["Appliances",*PAST_COLUMNS]]=999
        second=service.forecast(6,origin)
        assert [row["appliances_wh"] for row in first["predictions"]]==[row["appliances_wh"] for row in second["predictions"]]
        assert first["predictions"][0]["actual_wh"]!=second["predictions"][0]["actual_wh"]
    finally:
        service.frame=changed
        service.forecast.cache_clear()

def test_split_order(service):
    splits=service.metrics["splits"]
    assert splits["train"]["end"]<splits["validation"]["start"]
    assert splits["validation"]["end"]<splits["test"]["start"]
    best=min(service.metrics["comparison"],key=lambda name:service.metrics["comparison"][name]["validation"]["mae_wh"])
    assert best==service.artifact["name"]

@pytest.mark.parametrize("problem",["missing","duplicate","gap","negative"])
def test_dataset_validation(tmp_path,service,problem):
    raw=pd.read_csv(Path(__file__).resolve().parents[2]/"energydata_complete.csv").iloc[:1200].copy()
    if problem=="missing": raw.loc[20,"Appliances"]=None
    if problem=="duplicate": raw.loc[20,"date"]=raw.loc[19,"date"]
    if problem=="gap": raw=raw.drop(index=20)
    if problem=="negative": raw.loc[20,"Appliances"]=-10
    path=tmp_path/"bad.csv"
    raw.to_csv(path,index=False)
    with pytest.raises(ValueError): load_data(path)

def test_missing_dataset_has_actionable_error(tmp_path):
    with pytest.raises(FileNotFoundError,match="Restore the original"):
        load_data(tmp_path/"absent.csv")

def test_launcher_reports_startup_interrupt(monkeypatch,capsys):
    import runpy
    import uvicorn
    def interrupted(*args,**kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr(uvicorn,"run",interrupted)
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(Path(__file__).resolve().parents[1]/"run.py"),run_name="__main__")
    assert stopped.value.code==130
    output=capsys.readouterr().out
    assert "Loading scientific libraries" in output
    assert "Startup was interrupted" in output

@pytest.mark.parametrize("mode,unit",[("conditions","Wh per 10-minute interval"),("home","kWh per year")])
def test_manual_prediction_models_and_examples(client,mode,unit):
    report=client.get("/api/prediction/models")
    assert report.status_code==200,report.text
    model=report.json()[mode]
    assert model["unit"]==unit
    assert model["target_in_features"] is False
    assert "KWH" not in model["features"] and "Appliances" not in model["features"]
    assert sum(model["split_rows"].values())==model["rows"]
    assert model["interval"]["nominal_coverage"]==.8
    inputs=model["examples"][0]["inputs"]
    inputs={key:int(value) if key in {"occupants","home_type","heating_fuel","air_conditioning","month","day_of_week"} else value for key,value in inputs.items()}
    output=client.post("/api/prediction",json={"mode":mode,"inputs":inputs})
    assert output.status_code==200,output.text
    result=output.json()
    assert result["unit"]==unit and result["estimate"]>=0
    assert result["interval"]["lower"]<=result["estimate"]<=result["interval"]["upper"]
    assert (result["monthly_average_kwh"] is not None)==(mode=="home")

def test_manual_prediction_validation_and_domain_warning(client):
    data={"mode":"conditions","inputs":{"temperature_c":25,"humidity_percent":50,"lighting_wh":10,
        "outdoor_temperature_c":20,"hour":18,"day_of_week":0,"month":5}}
    assert client.post("/api/prediction",json=data).status_code==200
    data["inputs"]["humidity_percent"]=101
    assert client.post("/api/prediction",json=data).status_code==422
    data["inputs"]["humidity_percent"]=50
    data["inputs"]["temperature_c"]=55
    output=client.post("/api/prediction",json=data)
    assert any("outside the training range" in warning for warning in output.json()["warnings"])
    data["inputs"]["occupancy"]=5
    assert client.post("/api/prediction",json=data).status_code==422
    data["mode"]="mixed"
    assert client.post("/api/prediction",json=data).status_code==422

def test_authentication(client):
    headers=account(client,"alice@example.com")
    profile=client.get("/api/auth/me",headers=headers)
    assert profile.status_code==200
    assert profile.json()=={"email":"alice@example.com"}
    assert client.get("/api/auth/me").status_code==401
    assert client.get("/api/documents",headers=headers).status_code==200
    assert client.get("/api/documents").status_code==401
    assert client.get("/api/documents",headers={"Authorization":"Bearer invalid"}).status_code==401
    assert client.post("/api/auth/signup",json={"email":"alice@example.com","password":"StrongPassword123"}).status_code==409
    assert client.post("/api/auth/login",json={"email":"alice@example.com","password":"wrong"}).status_code==401

def test_private_document_isolation(client):
    alice=account(client,"alice@example.com")
    bob=account(client,"bob@example.com")
    result=client.post("/api/documents",headers=alice,files={"file":("private.txt",b"Zephyrometer household energy reading is 42 kWh. Private reference document.","text/plain")})
    assert result.status_code==201,result.text
    assert len(client.get("/api/documents",headers=alice).json()["documents"])==1
    assert client.get("/api/documents",headers=bob).json()["documents"]==[]
    private=client.post("/api/rag/query",headers=alice,json={"query":"Zephyrometer reading"}).json()
    assert any(row["private"] for row in private["sources"])
    public=client.post("/api/rag/query",headers=bob,json={"query":"Zephyrometer reading"}).json()
    assert not any(row["private"] for row in public["sources"])
    assert client.delete("/api/documents/private.txt",headers=bob).status_code==404
    assert client.delete("/api/documents/private.txt",headers=alice).status_code==200

def test_corrective_retrieval(client):
    weak=client.post("/api/rag/query",json={"query":"zzzzzz"}).json()
    assert not weak["sources"]
    assert [row["stage"] for row in weak["retrieval_trace"]]==["retrieve","grade","rewrite","retrieve","grade"]
    strong=client.post("/api/rag/query",json={"query":"LED lighting energy efficiency"}).json()
    assert strong["sources"]
    assert any(row["authority"] for row in strong["sources"])

def test_agent_tools(client):
    result=client.post("/api/agent/chat",json={"messages":[{"role":"user","content":"Why was consumption high yesterday?"}]})
    assert result.status_code==200,result.text
    data=result.json()
    assert data["reply"]
    assert len(data["tool_trace"])>=4
    assert data["mode"]=="local"

def test_bill_fields():
    result=analyze_bill("bill.txt",b"Billing period: May 2026\nTotal consumption: 250 kWh\nAmount due: INR 2000\nTariff: 8 per kWh\nDue date: 15 June")
    assert result["fields"]["total_kwh"]==250
    assert result["fields"]["amount"]==2000
    assert result["requires_confirmation"]
