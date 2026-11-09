import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_api(monkeypatch,tmp_path):
 b,_=train(synthetic(500));p=tmp_path/"m";joblib.dump(b,p);monkeypatch.setattr(api,"MODEL",p);r=TestClient(api.app).post("/v1/risk",json={"payment_id":"x","amount":500,"age_hours":3,"currency_mismatch":0,"reference_similarity":.9,"counterparty_risk":.1});assert r.status_code==200
