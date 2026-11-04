import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_interval(monkeypatch,tmp_path):
 b,_=train(synthetic(500));p=tmp_path/"m";joblib.dump(b,p);monkeypatch.setattr(api,"MODEL",p)
 r=TestClient(api.app).post("/v1/forecast",json={"sku_id":"x","price_index":1,"promo_active":1,"stockout_days":0,"recent_week_units":60,"season_index":1.1});v=r.json();assert r.status_code==200 and v["p10_units"]<=v["p90_units"]
