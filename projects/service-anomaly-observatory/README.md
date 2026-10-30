# Service Anomaly Observatory

An operational ML service for detecting abnormal service-health windows from latency, error rate, throughput, and saturation. Python trains an Isolation Forest and serves scored events; Java 17 illustrates alert-pipeline integration. The generator is synthetic.

## Features

* Robust median/IQR normalization and unsupervised anomaly scoring.
* Configured alert threshold stored alongside model metadata.
* `/metrics` counters for scored and alerted events.
* Dockerfile and CI workflow for standalone use.

```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/anomaly.joblib
uvicorn app.api:app --port 8000
```

Then run `cd java && javac -d out src/main/java/com/example/observatory/*.java && java -cp out com.example.observatory.AlertClient http://127.0.0.1:8000`.

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for safe operating policy.
