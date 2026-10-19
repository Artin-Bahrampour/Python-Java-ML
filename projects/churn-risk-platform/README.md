# Churn Risk Platform

A production-shaped, end-to-end machine-learning example for predicting customer churn from product usage and billing signals. Python owns training and inference; the dependency-free Java 17 client calls the scoring API and applies a human-review threshold.

> **Important:** The included generator creates synthetic data for demonstration and tests. Do not use synthetic scores for customer decisions.

## Architecture

```
CSV / warehouse extract -> Python training pipeline -> versioned model artifact
                                                   -> FastAPI /v1/predict
Java 17 client -----------------------------------> score + review decision
```

The training pipeline avoids leakage by fitting preprocessing only on the training split, selects a threshold on validation data, and saves model metadata with the artifact.

## Quick start

Requirements: Python 3.11+ and Java 17+ (Java is optional for API-only use).

```bash
cd python-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --generate-synthetic --output artifacts/churn_model.joblib
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd java-client
javac -d out src/main/java/com/example/churn/*.java
java -cp out com.example.churn.ChurnClient http://127.0.0.1:8000
```

## Verification

```bash
cd python-service
pytest -q
```

## API

`POST /v1/predict` accepts a customer record and returns `churn_probability`, the selected `threshold`, a boolean `requires_review`, and model metadata. Request validation deliberately rejects impossible or incomplete values.

See [docs/DESIGN.md](docs/DESIGN.md) for operations, data contract, and deployment guidance.
