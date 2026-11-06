import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.core import F
MODEL=Path(os.getenv("MODEL_PATH","artifacts/leak.joblib"));stats={"scored":0,"priority":0};app=FastAPI(title="Water Leak Risk")
class Segment(BaseModel):segment_id:str=Field(min_length=1);pressure_drop_bar:float=Field(ge=0);flow_cv:float=Field(ge=0);pipe_age_years:float=Field(ge=0);repairs_5y:int=Field(ge=0);soil_risk:float=Field(ge=0,le=1)
@app.post("/v1/risk")
def risk(x:Segment):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable")
 b=joblib.load(MODEL);p=float(b["model"].predict_proba(pd.DataFrame([{f:getattr(x,f) for f in F}]))[0,1]);alert=p>=b["threshold"];stats["scored"]+=1;stats["priority"]+=int(alert);return {"segment_id":x.segment_id,"leak_probability":round(p,5),"priority_inspection":alert,"model_version":b["model_version"]}
@app.get("/metrics")
def metrics():return stats
