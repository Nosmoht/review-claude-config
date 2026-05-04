.PHONY: validate lint format schema-validate token-budget test test-cov sync-marketplace-ref

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

validate: lint format schema-validate token-budget test

lint:
	ruff check hooks/ scripts/

format:
	ruff format --check hooks/ scripts/

schema-validate:
	$(PYTHON) scripts/validate_schema.py

token-budget:
	$(PYTHON) scripts/validate_token_budgets.py

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	$(PYTHON) -m pytest tests/ -v --tb=short --cov=hooks --cov=scripts --cov-report=term-missing

sync-marketplace-ref:
	$(PYTHON) scripts/sync_marketplace_ref.py
