from fastapi import FastAPI, HTTPException

from .detector import AnomalyDetector
from .logging_config import configure_logging
from .schemas import (
    HealthResponse,
    ScoreRequest,
    ScoreResponse,
    TrainingRequest,
    TrainingResponse,
)

configure_logging()

app = FastAPI(
    title="Service Health Anomaly Detector",
    version="0.1.0",
    description="Detect anomalous service-health telemetry using an unsupervised ML model.",
)

detector = AnomalyDetector()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_ready=detector.ready)


@app.post("/v1/model/train", response_model=TrainingResponse)
def train(request: TrainingRequest) -> TrainingResponse:
    try:
        samples = detector.train(request.observations)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TrainingResponse(trained=True, samples=samples)


@app.post("/v1/anomalies/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    try:
        results = detector.score(request.observations)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ScoreResponse(results=results)
