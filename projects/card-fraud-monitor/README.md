# Card Fraud Monitor

ML decision service for prioritising card transactions for fraud review. It performs chronological validation, compares a class-weighted logistic baseline with calibrated gradient boosting, uses an expected-cost threshold, and reports population-stability drift.

Run: \`cd python && pip install -r requirements.txt && python -m app.train && uvicorn app.api:app --port 8000\`.
