# Building Energy Forecast

An end-to-end demand-forecasting service for commercial-building electricity consumption. Python trains and exposes a next-day hourly demand model; Java 17 acts as a lightweight client for building-operations systems. The supplied generator creates synthetic data only.

## Architecture

`meter/weather extract -> Python model training -> versioned joblib artifact -> FastAPI /v1/forecast <- Java client`

## Run

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/energy.joblib
uvicorn app.api:app --port 8000
```

Then: `cd java && javac -d out src/main/java/com/example/energy/*.java && java -cp out com.example.energy.EnergyClient http://127.0.0.1:8000`.

Run tests: `cd python && pytest -q`. Design and operating controls are in [docs/DESIGN.md](docs/DESIGN.md).
