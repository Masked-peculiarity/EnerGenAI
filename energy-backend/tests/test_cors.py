import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.mark.parametrize("origin",[
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:8081", "http://127.0.0.1:8081",
])
def test_development_loopback_origins(monkeypatch,origin):
    monkeypatch.delenv("WEB_ORIGIN",raising=False)
    monkeypatch.setenv("APP_ENV","development")
    client=TestClient(create_app())
    response=client.options("/api/forecast",headers={
        "Origin":origin,"Access-Control-Request-Method":"POST",
        "Access-Control-Request-Headers":"Content-Type,Authorization",
    })
    assert response.status_code==200
    assert response.headers["access-control-allow-origin"]==origin

def test_custom_production_origin_remains_restricted(monkeypatch):
    monkeypatch.setenv("APP_ENV","production")
    monkeypatch.setenv("WEB_ORIGIN","https://energy.example.com")
    client=TestClient(create_app())
    for origin,status in [("https://energy.example.com",200),("http://127.0.0.1:8080",400),("https://untrusted.example",400)]:
        response=client.options("/api/forecast",headers={"Origin":origin,"Access-Control-Request-Method":"POST"})
        assert response.status_code==status
        if status==400:
            assert "access-control-allow-origin" not in response.headers
