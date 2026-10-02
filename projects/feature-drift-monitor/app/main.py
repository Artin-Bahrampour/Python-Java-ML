import json
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_session, init_db
from app.logging_config import configure_logging
from app.schemas import DriftRequest, DriftResponse, FeatureDrift
from app.service import DriftService
settings=get_settings(); configure_logging(settings.log_level); init_db(); app=FastAPI(title="Feature Drift Monitor",version="0.1.0")
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/v1/drift/analyze",response_model=DriftResponse)
def analyze_drift(payload: DriftRequest, session: Session=Depends(get_session)):
    if set(payload.reference.columns)!=set(payload.current.columns): raise HTTPException(422,"Reference and current columns must match.")
    report,features=DriftService(session).run(payload.reference.rows,payload.current.rows)
    return {"report_id":report.id,"reference_rows":report.reference_rows,"current_rows":report.current_rows,"drifted_features":report.drifted_features,"total_features":report.total_features,"features":[FeatureDrift(**f) for f in features]}
@app.get("/v1/drift/reports")
def list_reports(session: Session=Depends(get_session)):
    return [{"id":r.id,"created_at":r.created_at,"drifted_features":r.drifted_features,"total_features":r.total_features} for r in DriftService(session).repo.recent()]
@app.get("/v1/drift/reports/{report_id}")
def get_report(report_id:int,session:Session=Depends(get_session)):
    report=DriftService(session).get(report_id)
    if not report: raise HTTPException(404,"Report not found")
    return {"id":report.id,"reference_rows":report.reference_rows,"current_rows":report.current_rows,"features":json.loads(report.summary_json)}
