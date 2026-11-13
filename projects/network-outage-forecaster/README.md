# Network Outage Forecaster

ML service that prioritises telecom sites likely to suffer an outage in 24 hours. It uses a chronological split, logistic baseline, calibrated gradient boosting, cost-sensitive thresholding and PSI drift monitoring. Python serves decisions; Java 17 demonstrates NOC integration.

## Run
\`\`\`bash
cd python && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.train --output artifacts/outage.joblib
uvicorn app.api:app --port 8000
\`\`\`
See docs/DESIGN.md and docs/RUNBOOK.md.
