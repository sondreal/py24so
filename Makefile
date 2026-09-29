.PHONY: venv install install-dev test test-cov test-integration lint format generate check-spec build clean run-example

PYTHON ?= python3

all: install-dev test

venv:
	uv venv --python $(PYTHON)

install:
	uv pip install .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest tests/unit

test-cov:
	pytest --cov=py24so --cov-report=term-missing tests/unit

# Needs PY24SO_CLIENT_ID, PY24SO_CLIENT_SECRET and PY24SO_ORGANIZATION_ID
test-integration:
	pytest tests/integration

lint:
	black --check py24so tests scripts examples
	isort --check py24so tests scripts examples
	mypy
	python scripts/unasync.py --check

format:
	black py24so tests scripts examples
	isort py24so tests scripts examples

# Regenerate py24so/resources/_sync from py24so/resources/_async
generate:
	python scripts/unasync.py

# Compare the live OpenAPI spec with openapi/openapi.json
check-spec:
	python scripts/check_spec.py

build:
	uv build

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

run-example:
	$(PYTHON) examples/basic_usage.py
