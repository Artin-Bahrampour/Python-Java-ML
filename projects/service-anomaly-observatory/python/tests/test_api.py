import joblib
from fastapi.testclient import TestClient
from app import api
from app.core import synthetic,train
def test_score(monkeypatch,tmp_path):
 b,_=train(synthetic(500));p=tmp_path/"m";joblib.dump(b,p);monkeypatch.setattr(api,"MODEL",p);api.stats.update(scored=0,alerts=0)
 r=TestClient(api.app).post("/v1/score",json={"window_id":"x","p95_latency_ms":400,"error_rate":.1,"requests_per_second":100,"cpu_saturation":.9});assert r.status_code==200 and TestClient(api.app).get("/metrics").json()["scored"]==1
