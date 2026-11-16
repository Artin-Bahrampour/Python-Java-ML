import os,joblib
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .core import F,psi
app=FastAPI(title="Card Fraud Monitor")
MODEL_PATH=Path(os.getenv("MODEL_PATH","artifacts/fraud.joblib"))
if not MODEL_PATH.exists(): raise RuntimeError(f"model artifact missing: {MODEL_PATH}; run python -m app.train")
B=joblib.load(MODEL_PATH)
class Tx(BaseModel):
 amount:float=Field(gt=0,le=1e6);hour:int=Field(ge=0,le=23);merchant_risk:float=Field(ge=0,le=1);velocity_1h:int=Field(ge=0,le=100);international:int=Field(ge=0,le=1);card_age_days:int=Field(ge=0,le=10000)
@app.get("/health")
def health():return {"status":"ok","model_version":B["version"]}
@app.get("/metrics")
def metrics():return B["metrics"]|{"threshold":B["threshold"]}
@app.post("/v1/score")
def score(t:Tx):
 try:p=float(B["model"].predict_proba([[getattr(t,k) for k in F]])[0,1])
 except Exception as e:raise HTTPException(500,"scoring unavailable") from e
 return {"fraud_probability":round(p,5),"review_required":p>=B["threshold"],"model_version":B["version"]}
@app.post("/v1/drift/amount")
def drift(values:list[float]):
 if len(values)<20:raise HTTPException(422,"20 values required")
 v=psi(B["amount_ref"],values);return {"psi":round(v,4),"alert":v>=.2}
