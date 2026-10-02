# Feature Drift Monitor

Production-oriented ML feature drift monitoring service with PSI for numerical features, Jensen-Shannon divergence for categorical features, FastAPI, SQLite, CLI, tests, Docker, and CI.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli demo --rows 1000 --seed 42
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## CLI

```bash
python -m app.cli demo --rows 1000 --seed 42
python -m app.cli analyze --reference data/reference.csv --current data/current.csv
python -m app.cli export --report-id 1 --output drift-report.json
```

## Architecture

```text
Reference / Current Data -> Drift Engine -> Report -> Repository -> FastAPI
                               |\
                               | +-- PSI (numeric)
                               +---- JS divergence (categorical)
```

## API

- `GET /health`
- `POST /v1/drift/analyze`
- `GET /v1/drift/reports`
- `GET /v1/drift/reports/{report_id}`

Drift is a monitoring signal, not proof of model degradation. Production systems should combine it with data quality, model performance, and business metrics.

## Testing

```bash
pytest -q
```

## Docker

```bash
docker build -t feature-drift-monitor .
docker run --rm -p 8000:8000 feature-drift-monitor
```
