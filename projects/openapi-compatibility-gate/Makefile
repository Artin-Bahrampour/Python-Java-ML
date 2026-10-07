.PHONY: install test coverage example-compatible example-breaking

install:
	python -m pip install -e '.[dev]'

test:
	pytest

coverage:
	coverage run -m pytest && coverage report

example-compatible:
	oacg examples/baseline.yaml examples/candidate-compatible.yaml --report build/compatible-report.json

example-breaking:
	-oacg examples/baseline.yaml examples/candidate-breaking.yaml --report build/breaking-report.json
