.PHONY: validate lint format schema-validate test test-cov

validate: lint format schema-validate test

lint:
	ruff check hooks/ scripts/

format:
	ruff format --check hooks/ scripts/

schema-validate:
	python3 scripts/validate_schema.py

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=hooks --cov=scripts --cov-report=term-missing
