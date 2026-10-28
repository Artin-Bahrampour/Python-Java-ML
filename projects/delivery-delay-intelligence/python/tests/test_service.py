import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_prediction_and_metrics(monkeypatch,tmp_path):
 b,m=train(synthetic(500));assert m["auc"]>=0
 f=tmp_path/"m.joblib";joblib.dump(b,f);monkeypatch.setattr(api,"MODEL",f);api.seen.clear()
 r=TestClient(api.app).post("/v1/predict",json={"shipment_id":"x","carrier":"road","route_km":350,"package_kg":4,"weather_risk":.2,"weekday":3,"hub_backlog":15});assert r.status_code==200 and TestClient(api.app).get("/metrics/summary").json()["scored_requests"]==1
