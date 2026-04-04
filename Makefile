.PHONY: install dev lint format test build clean publish publish-test

install:
	poetry install --only main

dev:
	poetry install

lint:
	poetry run ruff check claude_cli/ tests/
	poetry run ruff format --check claude_cli/ tests/
	poetry run mypy claude_cli/

format:
	poetry run ruff check --fix claude_cli/ tests/
	poetry run ruff format claude_cli/ tests/

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=claude_cli --cov-report=html --cov-report=term

build: clean
	poetry build

clean:
	rm -rf dist/ build/ *.egg-info claude_cli/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

publish-test: build
	poetry publish -r testpypi

publish: build
	poetry publish
