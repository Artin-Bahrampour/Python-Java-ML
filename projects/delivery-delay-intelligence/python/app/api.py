import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.core import FEATURES
MODEL=Path(os.getenv("MODEL_PATH","artifacts/delay.joblib"));seen=[];app=FastAPI(title="Delivery Delay Intelligence",version="1.0.0")
class Shipment(BaseModel):
 shipment_id:str=Field(min_length=1);carrier:str;route_km:float=Field(ge=0,le=20000);package_kg:float=Field(ge=0,le=50000);weather_risk:float=Field(ge=0,le=1);weekday:int=Field(ge=0,le=6);hub_backlog:float=Field(ge=0,le=10000)
@app.get("/health")
def health():return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/predict")
def predict(x:Shipment):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable; train first")
 b=joblib.load(MODEL);row={f:getattr(x,f) for f in FEATURES};p=float(b["pipeline"].predict_proba(pd.DataFrame([row]))[0,1]);seen.append(p)
 return {"shipment_id":x.shipment_id,"delay_probability":round(p,6),"requires_attention":p>=b["threshold"],"model_version":b["model_version"]}
@app.get("/metrics/summary")
def metrics():return {"scored_requests":len(seen),"mean_delay_probability":round(sum(seen)/len(seen),4) if seen else None}
