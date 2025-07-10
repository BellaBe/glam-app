# services/credit-service/Makefile
.PHONY: help install dev test lint format clean build run docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install dev dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean cache files"
	@echo "  build       Build package"
	@echo "  run         Run development server"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run  Run with Docker Compose"

install:
	poetry install --no-dev

dev:
	poetry install
	poetry run pre-commit install

test:
	poetry run pytest -v --cov=src --cov-report=html

test-unit:
	poetry run pytest tests/ -v -m "not integration"

test-integration:
	poetry run pytest tests/ -v -m integration

lint:
	poetry run flake8 src tests
	poetry run mypy src
	poetry run black --check src tests
	poetry run isort --check src tests

format:
	poetry run black src tests
	poetry run isort src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

build:
	poetry build

run:
	poetry run uvicorn src.main:app --reload --port 8015 --log-level debug

run-prod:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8015

migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(name)"

migrate-downgrade:
	poetry run alembic downgrade -1

docker-build:
	docker build -t credit-service:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f credit-service

docker-test:
	docker-compose exec credit-service poetry run pytest

setup-dev: dev migrate
	@echo "Development environment ready!"

ci: lint test
	@echo "CI checks passed!"