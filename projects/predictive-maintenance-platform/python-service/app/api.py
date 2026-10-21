import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from app.model import FEATURES, load_bundle
from app.schemas import RiskResponse, Telemetry

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/maintenance_model.joblib"))
app = FastAPI(title="Predictive Maintenance Risk API", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.post("/v1/risk", response_model=RiskResponse)
def risk(telemetry: Telemetry) -> RiskResponse:
    if not MODEL_PATH.exists():
        raise HTTPException(503, "Model unavailable. Run python -m app.train --generate-synthetic first.")
    artifact = load_bundle(MODEL_PATH)
    row = pd.DataFrame([{field: getattr(telemetry, field) for field in FEATURES}])
    probability = float(artifact["pipeline"].predict_proba(row)[0, 1])
    return RiskResponse(asset_id=telemetry.asset_id, failure_risk_14d=round(probability, 6), intervention_threshold=artifact["threshold"], schedule_inspection=probability >= artifact["threshold"], model_version=artifact["model_version"])
