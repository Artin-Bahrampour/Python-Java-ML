# Service Health Anomaly Detector

A production-oriented Python service for detecting anomalous application-health signals from time-series telemetry.

## What this project demonstrates

- Python application architecture with a clean separation between API, domain logic, configuration, and ML
- FastAPI REST API with request validation
- Unsupervised anomaly detection using Isolation Forest
- Feature engineering from service telemetry
- Deterministic, testable anomaly-scoring logic
- Structured logging and environment-based configuration
- Unit/API tests with pytest
- Dockerized execution
- CI with GitHub Actions
- Explicit model training and prediction workflow
- Health/readiness endpoints suitable for service-oriented environments

## Problem

Real services produce signals such as latency, error rate, CPU utilization and request volume. A static threshold is often insufficient because normal behaviour changes with workload.

This project builds a small anomaly-detection service that:

1. accepts historical telemetry,
2. derives normalized features,
3. trains an Isolation Forest model,
4. scores new observations,
5. exposes anomaly decisions through an HTTP API.

The project is intentionally designed as an engineering portfolio project rather than a notebook-only ML experiment.

## Architecture

```text
Client
  |
  v
FastAPI
  |
  +--> Request validation
  |
  +--> Feature engineering
  |
  +--> Anomaly detector
  |       |
  |       +--> Isolation Forest
  |
  +--> Prediction response
```

The model is kept in memory for this small service. In a larger production system, model artifacts would normally be versioned and stored in object storage/model registry, with explicit model lifecycle management.

## Project structure

```text
service-health-anomaly-detector/
├── src/health_anomaly/
│   ├── api.py
│   ├── config.py
│   ├── logging_config.py
│   ├── schemas.py
│   ├── features.py
│   └── detector.py
├── tests/
│   ├── test_features.py
│   ├── test_detector.py
│   └── test_api.py
├── .github/workflows/ci.yml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.11+
- pip
- Docker (optional)

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn health_anomaly.api:app --app-dir src --reload
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Train a model

Send historical observations to:

```text
POST /v1/model/train
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/model/train \
  -H "Content-Type: application/json" \
  -d '{
    "observations": [
      {"latency_ms": 110, "error_rate": 0.01, "cpu_percent": 42, "requests_per_minute": 500},
      {"latency_ms": 115, "error_rate": 0.02, "cpu_percent": 44, "requests_per_minute": 520},
      {"latency_ms": 108, "error_rate": 0.01, "cpu_percent": 40, "requests_per_minute": 490},
      {"latency_ms": 112, "error_rate": 0.02, "cpu_percent": 43, "requests_per_minute": 510},
      {"latency_ms": 118, "error_rate": 0.01, "cpu_percent": 45, "requests_per_minute": 530},
      {"latency_ms": 1150, "error_rate": 0.35, "cpu_percent": 98, "requests_per_minute": 80}
    ]
  }'
```

Then score observations with:

```text
POST /v1/anomalies/score
```

## Run tests

```bash
pytest
```

The test suite covers feature construction, model lifecycle, validation and HTTP endpoints.

## Docker

Build:

```bash
docker build -t service-health-anomaly-detector .
```

Run:

```bash
docker run --rm -p 8000:8000 service-health-anomaly-detector
```

## Engineering decisions

### Why Isolation Forest?

The service does not assume labelled failure data. Isolation Forest is a practical unsupervised baseline for identifying observations that are structurally different from the training distribution.

### Why keep the model in memory?

This repository focuses on the service architecture and ML integration. A production deployment would separate model training from online serving and persist versioned model artifacts.

### Why FastAPI?

FastAPI provides typed request/response validation, automatic OpenAPI documentation, and a clean interface for a Python service.

## Production extensions

Possible next steps include:

- persistent model registry and model versioning
- Kafka/Redpanda telemetry ingestion
- Prometheus metrics
- OpenTelemetry tracing
- asynchronous batch scoring
- drift detection
- model performance monitoring
- PostgreSQL for prediction/audit history
- Kubernetes deployment
- authentication and authorization
- canary model rollout
