.PHONY: install test lint format-check generate train evaluate predict monitor docker-build

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .

generate:
	pv-forecast generate --output data/generated/pv_hourly.csv --days 730 --seed 42

train:
	pv-forecast train --data data/generated/pv_hourly.csv --artifacts-dir artifacts --seed 42

evaluate:
	pv-forecast evaluate --artifacts-dir artifacts

predict:
	pv-forecast predict --data data/generated/pv_hourly.csv --artifacts-dir artifacts --output artifacts/predictions.csv

monitor:
	pv-forecast monitor --reference data/generated/pv_hourly.csv --current data/generated/pv_hourly.csv --output artifacts/drift-report.json

docker-build:
	docker build -t solar-pv-generation-forecasting .
