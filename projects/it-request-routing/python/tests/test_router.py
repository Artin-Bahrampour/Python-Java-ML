import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_routes(monkeypatch,tmp_path):
 b,_=train(*synthetic());p=tmp_path/"m";joblib.dump(b,p);monkeypatch.setattr(api,"MODEL",p);r=TestClient(api.app).post("/v1/route",json={"ticket_id":"x","summary":"I cannot log into the corporate vpn"});assert r.status_code==200 and r.json()["suggested_queue"]=="access"
