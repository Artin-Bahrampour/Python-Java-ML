import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from app.model import FEATURES, load_bundle
from app.schemas import CustomerFeatures, Prediction

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/churn_model.joblib"))
app = FastAPI(title="Churn Risk API", version="1.0.0")


def bundle():
    if not MODEL_PATH.exists():
        raise HTTPException(503, "Model unavailable. Train it with python -m app.train --generate-synthetic")
    return load_bundle(MODEL_PATH)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.post("/v1/predict", response_model=Prediction)
def predict(customer: CustomerFeatures) -> Prediction:
    artifact = bundle()
    row = pd.DataFrame([{name: getattr(customer, name) for name in FEATURES}])
    probability = float(artifact["pipeline"].predict_proba(row)[0, 1])
    return Prediction(customer_id=customer.customer_id, churn_probability=round(probability, 6), threshold=artifact["threshold"], requires_review=probability >= artifact["threshold"], model_version=artifact["model_version"])
