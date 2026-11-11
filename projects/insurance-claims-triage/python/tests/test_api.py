from fastapi.testclient import TestClient
from app.api import app

def test_health_and_prediction():
    c=TestClient(app); assert c.get('/health').status_code == 200
    r=c.post('/v1/triage',json={'claim_amount':80000,'policy_age_days':20,'prior_claims':4,'incident_delay_days':35,'risk_region':1})
    assert r.status_code == 200 and 0 <= r.json()['risk_score'] <= 1

def test_rejects_invalid_amount():
    assert TestClient(app).post('/v1/triage',json={'claim_amount':0,'policy_age_days':1,'prior_claims':0,'incident_delay_days':0,'risk_region':0}).status_code == 422
