.PHONY: venv install install-dev install-http2 test test-cov lint format build clean publish publish-test

# Set default Python interpreter
PYTHON ?= python3

# Default target
all: install-dev test

# Environment setup
venv:
	uv venv --python $(PYTHON)
	@echo "Virtual environment created. Activate it with:"
	@echo "source .venv/bin/activate (Linux/macOS)"
	@echo ".venv\\Scripts\\activate (Windows)"

# Installation targets
install:
	uv pip install .

install-dev:
	uv pip install -e ".[dev,docs]"

install-http2:
	uv pip install -e ".[http2]"

# Testing targets
test:
	pytest

test-cov:
	pytest --cov=py24so

# Linting and formatting
lint:
	ruff check py24so tests examples
	mypy py24so tests examples

format:
	black py24so tests examples
	isort py24so tests examples

# Build targets
build:
	uv pip build

# Clean targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Publishing targets
publish:
	uv pip publish

publish-test:
	uv pip publish --repository=testpypi

# Helper for running the example
run-example:
	$(PYTHON) examples/basic_usage.py 