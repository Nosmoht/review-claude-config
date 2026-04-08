.PHONY: validate lint schema-validate test

validate: lint schema-validate test

lint:
	ruff check hooks/ scripts/

schema-validate:
	python3 scripts/validate_schema.py

test:
	pytest tests/ -v --tb=short
