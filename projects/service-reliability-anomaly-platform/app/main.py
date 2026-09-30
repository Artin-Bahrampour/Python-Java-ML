from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_session, init_db
from app.logging_config import configure_logging
from app.ml import AnomalyDetector
from app.schemas import TelemetryIn, TelemetryOut, ScoreOut, SummaryOut
from app.service import ReliabilityService

settings = get_settings()
configure_logging(settings.log_level)
init_db()

app = FastAPI(
    title="Service Reliability Anomaly Platform",
    version="0.1.0",
    description="API telemetry ingestion and anomaly detection service.",
)

detector = AnomalyDetector(settings.model_path, settings.anomaly_contamination)


def service(session: Session) -> ReliabilityService:
    return ReliabilityService(session, detector)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}


@app.get("/ready")
def ready():
    try:
        detector.load()
        return {"status": "ready", "model_version": detector.version}
    except FileNotFoundError:
        return {"status": "not_ready", "reason": "model_not_trained"}


@app.post("/v1/telemetry", response_model=TelemetryOut, status_code=201)
def ingest(payload: TelemetryIn, session: Session = Depends(get_session)):
    return service(session).ingest(payload)


@app.post("/v1/model/train")
def train(session: Session = Depends(get_session)):
    try:
        version = service(session).train()
        return {"status": "trained", "model_version": version}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/model/score", response_model=list[ScoreOut])
def score(
    limit: int = Query(default=100, ge=1, le=5000),
    session: Session = Depends(get_session),
):
    try:
        decisions = service(session).score_recent(limit)
        return [
            {
                "telemetry_id": d.telemetry_id,
                "score": d.score,
                "is_anomaly": bool(d.is_anomaly),
                "model_version": d.model_version,
            }
            for d in decisions
        ]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/v1/services/{service_name}/summary", response_model=SummaryOut)
def summary(
    service_name: str,
    hours: int = Query(default=24, ge=1, le=168),
    session: Session = Depends(get_session),
):
    return service(session).summary(service_name, hours)
