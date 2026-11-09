# Payment Reconciliation Risk

An ML service that prioritizes payment records needing reconciliation review. Python trains an imbalanced classifier and exposes a guarded API; Java 17 demonstrates ledger integration. Data is synthetic.

Includes precision/recall validation, a confidence threshold, metrics, Dockerfile, CI and operating guidance.

```bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --synthetic --output artifacts/recon.joblib
uvicorn app.api:app --port 8000
```
