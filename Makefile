# PullData Development Makefile

.PHONY: help install install-dev test test-cov lint format type-check clean docs

help:
	@echo "PullData Development Commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linter (ruff)"
	@echo "  make format        - Format code (black)"
	@echo "  make type-check    - Run type checker (mypy)"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make pre-commit    - Run all pre-commit checks"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -v

test-cov:
	pytest --cov=pulldata --cov-report=term-missing --cov-report=html

lint:
	ruff check pulldata/

format:
	black pulldata/
	ruff check --fix pulldata/

type-check:
	mypy pulldata/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

pre-commit:
	pre-commit run --all-files

docs:
	cd docs && make html
