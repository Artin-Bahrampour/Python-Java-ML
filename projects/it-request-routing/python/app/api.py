import os,joblib
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
MODEL=Path(os.getenv("MODEL_PATH","artifacts/router.joblib"));stats={"scored":0,"manual_review":0,"confidence_sum":0.0};app=FastAPI(title="IT Request Routing")
class Request(BaseModel):ticket_id:str=Field(min_length=1);summary:str=Field(min_length=8,max_length=2000)
@app.get("/health")
def health():return {"status":"ok","model_loaded":MODEL.exists()}
@app.post("/v1/route")
def route(x:Request):
 if not MODEL.exists():raise HTTPException(503,"Model unavailable; train first")
 b=joblib.load(MODEL);probs=b["pipeline"].predict_proba([x.summary])[0];i=int(probs.argmax());confidence=float(probs[i]);label=b["pipeline"].classes_[i];manual=confidence<b["confidence_threshold"];stats["scored"]+=1;stats["manual_review"]+=int(manual);stats["confidence_sum"]+=confidence
 return {"ticket_id":x.ticket_id,"queue":"manual_review" if manual else label,"suggested_queue":label,"confidence":round(confidence,4),"model_version":b["model_version"]}
@app.get("/metrics")
def metrics():return {**stats,"mean_confidence":round(stats["confidence_sum"]/stats["scored"],4) if stats["scored"] else None}
