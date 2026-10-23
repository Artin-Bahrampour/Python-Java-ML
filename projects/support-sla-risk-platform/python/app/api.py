import os, joblib, pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from app.schemas import Ticket, Risk
from app.train import FEATURES
MODEL=Path(os.getenv("MODEL_PATH","artifacts/sla.joblib")); app=FastAPI(title="Support SLA Risk API",version="1.0.0")
@app.get("/health")
def health(): return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/risk",response_model=Risk)
def risk(ticket:Ticket):
    if not MODEL.exists(): raise HTTPException(503,"Model unavailable; train first")
    b=joblib.load(MODE); p=float(b["pipeline"].predict_proba(pd.DataFrame([{f:getattr(ticket,f) for f in FEATURES}]))[0,1])
    return Risk(ticket_id=ticket.ticket_id,breach_probability=round(p,6),threshold=b["threshold"],prioritize=p>=b["threshold"],model_version=b["model_version"])
