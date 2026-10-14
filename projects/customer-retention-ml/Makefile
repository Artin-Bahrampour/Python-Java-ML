.PHONY: test lint format-check train predict
test:
	pytest
lint:
	ruff check .
format-check:
	ruff format --check .
train:
	churn-ml generate --output data/generated/customers.csv --rows 5000
	churn-ml train --data data/generated/customers.csv --artifacts-dir artifacts
	churn-ml evaluate --artifacts-dir artifacts
predict:
	churn-ml predict --data data/generated/customers.csv --artifacts-dir artifacts --output artifacts/scores.csv
