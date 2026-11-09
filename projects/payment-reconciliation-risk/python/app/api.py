import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.core import F
MODEL=Path(os.getenv("MODEL_PATH","artifacts/recon.joblib"));stats={"scored":0,"review":0};app=FastAPI(title="Payment Reconciliation Risk")
class Payment(BaseModel):payment_id:str=Field(min_length=1);amount:float=Field(ge=0);age_hours:float=Field(ge=0);currency_mismatch:int=Field(ge=0,le=1);reference_similarity:float=Field(ge=0,le=1);counterparty_risk:float=Field(ge=0,le=1)
@app.post("/v1/risk")
def risk(x:Payment):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable")
 b=joblib.load(MODEL);p=float(b["model"].predict_proba(pd.DataFrame([{f:getattr(x,f) for f in F}]))[0,1]);review=p>=b["threshold"];stats["scored"]+=1;stats["review"]+=int(review);return {"payment_id":x.payment_id,"risk":round(p,5),"manual_review":review,"model_version":b["model_version"]}
@app.get("/metrics")
def metrics():return stats
