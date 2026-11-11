from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .core import FEATURES, fit, sample

app=FastAPI(title="Claims Triage API", version="1.0")
BUNDLE=fit(*sample())
class Claim(BaseModel):
    claim_amount: float = Field(gt=0, le=2_000_000)
    policy_age_days: int = Field(ge=0, le=20_000)
    prior_claims: int = Field(ge=0, le=100)
    incident_delay_days: int = Field(ge=0, le=3650)
    risk_region: int = Field(ge=0, le=1)

@app.get("/health")
def health(): return {"status":"ok","model_version":BUNDLE["version"]}
@app.get("/metrics")
def metrics(): return BUNDLE["metrics"] | {"threshold":BUNDLE["threshold"]}
@app.post("/v1/triage")
def triage(claim: Claim):
    try: probability=float(BUNDLE["model"].predict_proba([[getattr(claim,f) for f in FEATURES]])[0,1])
    except Exception as exc: raise HTTPException(500,"prediction unavailable") from exc
    return {"risk_score":round(probability,4),"review_required":probability >= BUNDLE["threshold"],"model_version":BUNDLE["version"]}
