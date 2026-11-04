# Inventory Demand Forecast

An inventory-planning ML service that predicts next-week unit demand **with an 80% uncertainty interval**. Python trains quantile models and serves forecasts; Java 17 demonstrates ERP integration. Synthetic data is included for local development only.

## Capabilities

* Quantile gradient-boosting models for P10, P50 and P90 demand.
* Validation MAE and empirical interval coverage stored with the artifact.
* API guardrails and request/interval-width metrics.
* Dockerfile, CI and operating guidance.

```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/demand.joblib
uvicorn app.api:app --port 8000
```

Run the Java client with `cd java && javac -d out src/main/java/com/example/inventory/*.java && java -cp out com.example.inventory.ForecastClient http://127.0.0.1:8000`.
