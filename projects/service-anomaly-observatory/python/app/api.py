import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.core import FEATURES
MODEL=Path(os.getenv("MODEL_PATH","artifacts/anomaly.joblib"));stats={"scored":0,"alerts":0};app=FastAPI(title="Service Anomaly Observatory")
class Window(BaseModel):
 window_id:str=Field(min_length=1);p95_latency_ms:float=Field(ge=0);error_rate:float=Field(ge=0,le=1);requests_per_second:float=Field(ge=0);cpu_saturation:float=Field(ge=0,le=1)
@app.get("/health")
def health():return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/score")
def score(x:Window):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable; train first")
 b=joblib.load(MODEL);value=float(-b["model"].score_samples(pd.DataFrame([{f:getattr(x,f) for f in FEATURES}]))[0]);alert=value>=b["threshold"];stats["scored"]+=1;stats["alerts"]+=int(alert)
 return {"window_id":x.window_id,"anomaly_score":round(value,6),"threshold":round(b["threshold"],6),"alert":alert,"model_version":b["model_version"]}
@app.get("/metrics")
def metrics():return stats
