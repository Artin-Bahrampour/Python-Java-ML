# Delivery Delay Intelligence

An operational ML service that estimates whether a shipment will miss its promised delivery window. Python handles versioned training, inference, and drift snapshots; Java 17 demonstrates how an order-management client calls the service. Synthetic data is supplied for local use only.

## Architecture

`event export -> training + validation -> joblib artifact -> FastAPI /v1/predict <- Java OMS client`

The API also exposes `/metrics/summary` for request counts and prediction-distribution monitoring. A GitHub Actions workflow runs the Python test suite and Java compilation.

## Local run

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/delay.joblib
uvicorn app.api:app --port 8000
```

In another terminal: `cd java && javac -d out src/main/java/com/example/delivery/*.java && java -cp out com.example.delivery.DeliveryClient http://127.0.0.1:8000`.

Run tests with `cd python && pytest -q`. See [docs/OPERATIONS.md](docs/OPERATIONS.md).
