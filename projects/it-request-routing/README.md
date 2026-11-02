# IT Request Routing Service

A calibrated text-classification service that routes internal IT requests to `access`, `hardware`, `network`, or `software` queues. Python provides training, validation and a FastAPI interface; Java 17 shows an integration client. The dataset is synthetic and has no production tickets.

## Production shape

* TF-IDF + calibrated linear classifier with stratified validation metrics.
* Explicit confidence threshold; low-confidence tickets route to `manual_review`.
* Request counters and confidence summary at `/metrics`.
* Dockerfile and a standalone CI workflow.

```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/router.joblib
uvicorn app.api:app --port 8000
```

Then: `cd java && javac -d out src/main/java/com/example/routing/*.java && java -cp out com.example.routing.RoutingClient http://127.0.0.1:8000`.

See [docs/OPERATIONS.md](docs/OPERATIONS.md).
