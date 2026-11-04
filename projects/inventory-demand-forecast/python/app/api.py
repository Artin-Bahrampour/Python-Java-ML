import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.core import FEATURES
MODEL=Path(os.getenv("MODEL_PATH","artifacts/demand.joblib"));stats={"requests":0,"interval_width_sum":0.0};app=FastAPI(title="Inventory Demand Forecast")
class Item(BaseModel):sku_id:str=Field(min_length=1);price_index:float=Field(gt=0);promo_active:int=Field(ge=0,le=1);stockout_days:int=Field(ge=0,le=365);recent_week_units:float=Field(ge=0);season_index:float=Field(gt=0)
@app.get("/health")
def health():return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/forecast")
def forecast(x:Item):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable; train first")
 b=joblib.load(MODEL);row=pd.DataFrame([{f:getattr(x,f) for f in FEATURES}]);a,m,z=[max(0,float(b["models"][q].predict(row)[0])) for q in (.1,.5,.9)];a,z=min(a,z),max(a,z);stats["requests"]+=1;stats["interval_width_sum"]+=z-a
 return {"sku_id":x.sku_id,"p10_units":round(a,2),"p50_units":round(m,2),"p90_units":round(z,2),"model_version":b["model_version"]}
@app.get("/metrics")
def metrics():return {**stats,"mean_interval_width":round(stats["interval_width_sum"]/stats["requests"],2) if stats["requests"] else None}
