from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health():
    r=client.get("/health"); assert r.status_code==200 and r.json()["status"]=="ok"
def test_drift_endpoint():
    p={"reference":{"columns":["age","region"],"rows":[{"age":20,"region":"A"},{"age":21,"region":"A"},{"age":22,"region":"A"}]},"current":{"columns":["age","region"],"rows":[{"age":60,"region":"B"},{"age":61,"region":"B"},{"age":62,"region":"B"}]}}
    r=client.post("/v1/drift/analyze",json=p); assert r.status_code==200 and r.json()["total_features"]==2
