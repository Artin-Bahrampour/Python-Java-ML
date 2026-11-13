from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .core import FEATURES,make_data,psi,train
app=FastAPI(title="Network Outage Forecaster");BUNDLE=train(*make_data()[:2])
class Telemetry(BaseModel):
 signal_drop_db:float=Field(ge=0,le=60);packet_loss_pct:float=Field(ge=0,le=100);latency_ms:float=Field(ge=0,le=5000);weather_severity:int=Field(ge=0,le=3);site_age_years:int=Field(ge=0,le=80);alarms_6h:int=Field(ge=0,le=100)
@app.get("/health")
def health():return {"status":"ok","model_version":BUNDLE["version"]}
@app.get("/metrics")
def metrics():return BUNDLE["metrics"]|{"threshold":BUNDLE["threshold"]}
@app.post("/v1/forecast")
def forecast(t:Telemetry):
 try:p=float(BUNDLE["model"].predict_proba([[getattr(t,f) for f in FEATURES]])[0,1])
 except Exception as e:raise HTTPException(500,"prediction unavailable") from e
 return {"outage_risk":round(p,4),"dispatch_recommended":p>=BUNDLE["threshold"],"model_version":BUNDLE["version"]}
@app.post("/v1/drift/signal")
def drift(values:list[float]):
 if len(values)<20:raise HTTPException(422,"at least 20 readings required")
 v=psi(BUNDLE["reference_signal"],values);return {"psi":round(v,4),"alert":v>=.2}
