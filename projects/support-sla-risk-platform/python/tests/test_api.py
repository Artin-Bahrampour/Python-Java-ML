import joblib
from fastapi.testclient import TestClient
from app import api
from app.train import synthetic,train
def test_endpoint(monkeypatch,tmp_path):
    b,_=train(synthetic(400)); path=tmp_path/"m.joblib"; joblib.dump(b,path); monkeypatch.setattr(api,"MODEL",path)
    r=TestClient(api.app).post("/v1/risk",json={"ticket_id":"x","priority":"urgent","channel":"email","age_minutes":120,"messages_count":5,"customer_tier":"enterprise","agent_queue_depth":20}); assert r.status_code==200 and 0<=r.json()["breach_probability"]<=1
