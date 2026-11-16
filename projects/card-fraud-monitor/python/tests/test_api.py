from fastapi.testclient import TestClient
from app.api import app
def test_score():
 r=TestClient(app).post("/v1/score",json={"amount":900,"hour":2,"merchant_risk":.9,"velocity_1h":4,"international":1,"card_age_days":8});assert r.status_code==200 and 0<=r.json()["fraud_probability"]<=1
