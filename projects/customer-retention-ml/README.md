# Customer Retention ML: Churn Risk Modeling

A reproducible machine-learning workflow for customer churn-risk estimation. It compares logistic regression as a transparent baseline with a random forest, evaluates both on held-out data, persists preprocessing and model pipelines, and supports batch scoring.

## Business problem
Retention teams need to prioritize outreach. This project demonstrates a classification workflow that evaluates unseen examples with metrics beyond accuracy. The bundled dataset generator creates deterministic synthetic records; results demonstrate engineering, not real commercial performance.

## Engineering highlights
- Deterministic synthetic data and strict input validation.
- Stratified train/test split and reproducible seed.
- Shared preprocessing pipelines: numeric imputation/scaling and categorical one-hot encoding.
- Logistic-regression baseline vs. random-forest candidate.
- ROC-AUC, average precision, precision, recall, F1, Brier score, and confusion matrix.
- Persisted model bundle, batch inference, tests, Docker, CI, model card, and operational notes.

## Quick start (Python 3.11+)
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
make test
make train
make predict
```

## CLI
```bash
churn-ml generate --output data/generated/customers.csv --rows 5000
churn-ml train --data data/generated/customers.csv --artifacts-dir artifacts
churn-ml evaluate --artifacts-dir artifacts
churn-ml predict --data data/generated/customers.csv --artifacts-dir artifacts --output artifacts/scores.csv
```
Artifacts are written to `artifacts/` and excluded from Git.

## Architecture
```text
Synthetic customer data -> schema validation -> stratified split
   -> logistic regression baseline + random forest candidate
   -> held-out evaluation -> persisted pipeline -> batch risk scores
```

## Evaluation policy
The report contains ROC-AUC and average precision plus threshold-dependent precision, recall, F1, confusion matrix, and Brier score. Churn can be imbalanced, so accuracy alone is insufficient. Threshold 0.5 is illustrative; choose an operational threshold based on intervention capacity and error costs. The report flags which model has higher ROC-AUC but metrics must be reviewed before promotion.

## Input schema
`tenure_months`, `monthly_spend`, `support_tickets_90d`, `late_payments_12m`, `usage_days_30d`, `plan_type`, `contract_type`, `autopay`, and (for training) `churned`.

## Docker
```bash
docker build -t customer-retention-ml .
docker run --rm customer-retention-ml --help
```

## Security and limitations
Do not commit production customer data, secrets, or model artifacts. A risk score is not a causal explanation or an automatic decision. Synthetic-to-real distribution shift, lack of temporal evaluation, and absence of causal uplift modeling are key limitations. Production use requires real-data validation, temporal backtesting, calibration, subgroup error analysis, monitoring, versioning, and rollback procedures. Treat `joblib` bundles as trusted artifacts; never load untrusted model files.
