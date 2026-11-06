import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_risk(monkeypatch,tmp_path):
 b,_=train(synthetic(500));f=tmp_path/"m";joblib.dump(b,f);monkeypatch.setattr(api,"MODEL",f);r=TestClient(api.app).post("/v1/risk",json={"segment_id":"x","pressure_drop_bar":.3,"flow_cv":.2,"pipe_age_years":22,"repairs_5y":1,"soil_risk":.4});assert r.status_code==200
