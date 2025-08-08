.PHONY: help install dev test clean docker-build docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests"
	@echo "  make migrate     - Run database migrations"
	@echo "  make clean       - Clean up generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up   - Start services with docker-compose"
	@echo "  make docker-down - Stop docker-compose services"

install:
	poetry install
	pre-commit install
	prisma generate

dev:
	poetry run python -m src.main

test:
	poetry run pytest -v

test-cov:
	poetry run pytest --cov=src --cov-report=html --cov-report=term

migrate:
	poetry run prisma migrate dev

migrate-deploy:
	poetry run prisma migrate deploy

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache

docker-build:
	docker build -t webhook-service:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f webhook-service

lint:
	poetry run black src tests
	poetry run isort src tests
	poetry run flake8 src tests
	poetry run mypy src

pre-commit:
	pre-commit run --all-files


