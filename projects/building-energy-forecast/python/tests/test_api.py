import joblib
from fastapi.testclient import TestClient
from app import api
from app.train import synthetic,train
def test_forecast(monkeypatch,tmp_path):
 b,_=train(synthetic(500));f=tmp_path/"m.joblib";joblib.dump(b,f);monkeypatch.setattr(api,"MODEL",f)
 r=TestClient(api.app).post("/v1/forecast",json={"building_id":"B-1","hour":9,"day_of_week":2,"outside_temp_c":4,"occupancy_ratio":.8,"prior_hour_kwh":143});assert r.status_code==200 and r.json()["predicted_kwh"]>=0
