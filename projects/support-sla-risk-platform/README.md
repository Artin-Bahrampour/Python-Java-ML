# Support SLA Risk Platform

A production-shaped ML service that ranks support tickets by their likelihood of breaching a response SLA. Python owns training/inference and Java 17 demonstrates operational integration. The bundled dataset is synthetic and intended for demonstration only.

## Architecture

`ticket export -> training pipeline -> versioned artifact -> FastAPI /v1/risk <- Java triage client`

The model is trained with transformations fit on the training split only. Threshold selection maximizes recall subject to a precision floor, so high-risk tickets can be routed to a human queue.

## Run

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/sla.joblib
uvicorn app.api:app --port 8000
```

In another terminal:

```bash
cd java
javac -d out src/main/java/com/example/sla/*.java
java -cp out com.example.sla.SlaClient http://127.0.0.1:8000
```

Run Python tests with `cd python && pytest -q`. See [docs/DESIGN.md](docs/DESIGN.md).
