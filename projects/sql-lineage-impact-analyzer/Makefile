.PHONY: install test lint analyze docker-build

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	ruff check src tests

analyze:
	lineage-guard analyze --models-dir examples/models --dialect postgres --format text

docker-build:
	docker build -t sql-lineage-impact-analyzer:local .
