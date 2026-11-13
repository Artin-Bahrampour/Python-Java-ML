from fastapi.testclient import TestClient
from app.api import app
def test_forecast():
 r=TestClient(app).post("/v1/forecast",json={"signal_drop_db":12,"packet_loss_pct":7,"latency_ms":100,"weather_severity":2,"site_age_years":4,"alarms_6h":3});assert r.status_code==200 and 0<=r.json()["outage_risk"]<=1
def test_drift_validation():assert TestClient(app).post("/v1/drift/signal",json=[1.0]*3).status_code==422
