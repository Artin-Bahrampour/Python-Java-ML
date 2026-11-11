# Insurance Claims Triage

Production-style ML service for prioritising insurance claims that deserve manual review. Python trains and serves a calibrated risk model; the Java 17 client represents a claims-workflow integration.

## Run
```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --output artifacts/claims.joblib
uvicorn app.api:app --port 8000
```
Then run `java/src/main/java/com/example/claims/ClaimsClient.java` with Java 17. See `docs/OPERATIONS.md` for decisions, limits and deployment notes.
