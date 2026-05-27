.PHONY: validate lint format schema-validate token-budget validate-descriptions check-scaffold-quality test test-cov sync-marketplace-ref

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)

validate: lint format schema-validate token-budget validate-descriptions test

lint:
	ruff check hooks/ scripts/
	@if ls bin/*.sh >/dev/null 2>&1; then \
		shellcheck bin/*.sh; \
	fi

format:
	ruff format --check hooks/ scripts/

schema-validate:
	$(PYTHON) scripts/validate_schema.py

token-budget:
	$(PYTHON) scripts/validate_token_budgets.py

validate-descriptions:
	PYTHON=$(PYTHON) bash bin/run-validate-descriptions.sh

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov:
	$(PYTHON) -m pytest tests/ -v --tb=short --cov=hooks --cov=scripts --cov-report=term-missing

check-scaffold-quality:
	$(PYTHON) scripts/check_scaffold_quality.py
	$(PYTHON) scripts/check_scaffold_quality.py --verify-matrix-complete

sync-marketplace-ref:
	bash bin/sync-marketplace-ref.sh
