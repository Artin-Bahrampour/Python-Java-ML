# Predictive Maintenance Platform

An end-to-end maintenance-risk service for industrial pumps. It estimates the probability of a bearing-related failure in the next 14 days from recent telemetry. Python trains and serves the model; a dependency-free Java 17 client integrates the risk response with a maintenance workflow.

The included data generator is synthetic and intended only for local demonstration. It is not a substitute for validated production telemetry or a safety system.

## Architecture

```
Telemetry extract -> Python training pipeline -> versioned artifact -> FastAPI /v1/risk
Java 17 maintenance client ----------------------------------------> work-order routing
```

The training pipeline uses a stratified holdout split, fits transformations only on training data, selects a validation threshold using recall subject to a precision floor, and saves metrics with the model.

## Run locally

Requirements: Python 3.11+ and Java 17+.

```bash
cd python-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --generate-synthetic --output artifacts/maintenance_model.joblib
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd java-client
javac -d out src/main/java/com/example/maintenance/*.java
java -cp out com.example.maintenance.MaintenanceClient http://127.0.0.1:8000
```

## Validate

```bash
cd python-service
pytest -q
```

See [docs/DESIGN.md](docs/DESIGN.md) for the data contract, monitoring, governance, and deployment model.
