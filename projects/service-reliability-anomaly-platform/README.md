# Service Reliability Anomaly Platform

A production-oriented Python service for detecting anomalous API/service telemetry and exposing operational insights through a REST API.

## Why this project

This project models a realistic reliability workflow:

- ingest service metrics/events
- persist observations in SQLite
- validate and normalize telemetry
- score anomalies with an Isolation Forest model
- expose health, ingestion, scoring, and summary endpoints
- retain model metadata and anomaly decisions
- provide structured logging and configuration
- ship with Docker and GitHub Actions CI
- include deterministic tests and an evaluation script

It is intentionally designed as a portfolio project rather than a tutorial toy.

## Architecture

```text
Client / Monitoring Agent
          |
          v
      FastAPI API
          |
   +------+------+
   |             |
Validation     Service Layer
                 |
        +--------+--------+
        |                 |
   SQLite Repository   ML Detector
        |                 |
        +--------+--------+
                 |
          anomaly decisions
```

## Features

- FastAPI REST API
- Pydantic request/response validation
- SQLite persistence through SQLAlchemy
- Isolation Forest anomaly detection
- deterministic synthetic telemetry generator
- model training and scoring service
- configurable anomaly contamination
- structured application logging
- Docker image
- GitHub Actions CI
- pytest test suite
- evaluation CLI with precision/recall/F1
- health/readiness endpoints

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Run tests

```bash
pytest -q
```

## Generate demo telemetry

```bash
python -m app.cli generate-data --count 500 --seed 42
```

## Train the detector

```bash
python -m app.cli train
```

## Score recent telemetry

```bash
python -m app.cli score --limit 100
```

## Evaluate

```bash
python -m app.cli evaluate --count 1000 --seed 42
```

## Docker

```bash
docker build -t service-reliability-anomaly-platform .
docker run --rm -p 8000:8000 service-reliability-anomaly-platform
```

## API examples

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Ingest telemetry

```bash
curl -X POST http://127.0.0.1:8000/v1/telemetry   -H "Content-Type: application/json"   -d '{
    "service": "payments-api",
    "timestamp": "2026-09-30T10:00:00Z",
    "latency_ms": 850,
    "error_rate": 0.18,
    "requests_per_minute": 140,
    "cpu_percent": 92,
    "memory_percent": 78
  }'
```

### Summary

```bash
curl "http://127.0.0.1:8000/v1/services/payments-api/summary?hours=24"
```

## Configuration

Environment variables:

- `APP_ENV` (default: `development`)
- `DATABASE_URL` (default: `sqlite:///./data/telemetry.db`)
- `MODEL_PATH` (default: `./data/model.joblib`)
- `ANOMALY_CONTAMINATION` (default: `0.05`)
- `LOG_LEVEL` (default: `INFO`)

## Engineering notes

The detector uses an Isolation Forest because labeled production incidents are often scarce. The application therefore separates:

1. telemetry collection,
2. feature extraction,
3. unsupervised model training,
4. anomaly scoring,
5. persistence and API presentation.

For a real production deployment, the next steps would include PostgreSQL, a message broker, model/version registry, drift monitoring, authentication, rate limiting, and OpenTelemetry integration.
