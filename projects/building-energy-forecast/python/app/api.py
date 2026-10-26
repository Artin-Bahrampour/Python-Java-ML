import os,joblib,pandas as pd
from pathlib import Path
from fastapi import FastAPI,HTTPException
from app.schemas import ForecastRequest,Forecast
from app.train import FEATURES
MODEL=Path(os.getenv("MODEL_PATH","artifacts/energy.joblib"));app=FastAPI(title="Building Energy Forecast API",version="1.0.0")
@app.get("/health")
def health():return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/forecast",response_model=Forecast)
def forecast(request:ForecastRequest):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable; train first")
 b=joblib.load(MODEL);v=float(b["model"].predict(pd.DataFrame([{f:getattr(request,f) for f in FEATURES}]))[0])
 return Forecast(building_id=request.building_id,predicted_kwh=round(max(v,0),3),model_version=b["model_version"])
