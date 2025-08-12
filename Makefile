# Makefile for Glam App Monorepo

# Service directories (auto-detect)
SERVICE_DIRS := $(shell find services -maxdepth 1 -type d -name "*-service" -o -name "*-ai-*" -o -name "*-connector" -o -name "*-cache" | sort)
SERVICE_NAMES := $(shell find services -maxdepth 1 -type d \( -name "*-service" -o -name "*-ai-*" -o -name "*-connector" -o -name "*-cache" \) -exec basename {} \; | sort)

# Docker compose files
LOCAL_COMPOSE = docker-compose.local.yml
DEV_COMPOSE = docker-compose.dev.yml
PROD_COMPOSE = docker-compose.prod.yml

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

# Default environment file
ENV_FILE ?= .env

.PHONY: help
help:
	@echo "$(BLUE)╔════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║       Glam App - Monorepo Management       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)🏗️  Infrastructure (docker-compose.local.yml):$(NC)"
	@echo "  make dev            Start infrastructure (DBs, NATS, Redis, MinIO)"
	@echo "  make dev-down       Stop infrastructure"
	@echo "  make dev-logs       Show infrastructure logs"
	@echo "  make dev-clean      Remove infrastructure + volumes"
	@echo ""
	@echo "$(YELLOW)💻 Local Development (run services on host):$(NC)"
	@echo "  make run SERVICE=webhook-service    Run single service"
	@echo "  make run-all                        Run all services in parallel"
	@echo "  make setup SERVICE=webhook-service  Setup service (install deps + prisma)"
	@echo ""
	@echo "$(YELLOW)🐳 Docker Development (docker-compose.yml):$(NC)"
	@echo "  make docker-dev     Start all services in Docker"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-down    Stop Docker stack"
	@echo "  make docker-logs    Show Docker logs"
	@echo ""
	@echo "$(YELLOW)🚀 Production (docker-compose.prod.yml):$(NC)"
	@echo "  make prod           Start production stack"
	@echo "  make prod-build     Build production images"
	@echo "  make prod-down      Stop production stack"
	@echo ""
	@echo "$(YELLOW)🗄️  Database:$(NC)"
	@echo "  make db-push SERVICE=webhook-service    Push Prisma schema"
	@echo "  make db-migrate SERVICE=webhook-service Create migration"
	@echo "  make db-url SERVICE=webhook-service     Show DATABASE_URL"
	@echo ""
	@echo "$(YELLOW)📦 Available services:$(NC)"
	@for service in $(SERVICE_NAMES); do echo "  • $$service"; done

# ─────────────────────────────────────────────────
# Infrastructure Management (Local Development)
# ─────────────────────────────────────────────────

dev:
	@echo "$(GREEN)🚀 Starting local infrastructure...$(NC)"
	@docker compose -f $(LOCAL_COMPOSE) --env-file $(ENV_FILE) up -d
	@echo "$(GREEN)✅ Infrastructure ready!$(NC)"
	@echo ""
	@echo "$(BLUE)📡 Services:$(NC)"
	@echo "  • NATS:       http://localhost:4222 (client) | http://localhost:8222 (monitoring)"
	@echo "  • Redis:      localhost:6379"
	@echo "  • MailHog:    http://localhost:8025 (UI) | localhost:1025 (SMTP)"
	@echo "  • MinIO:      http://localhost:9001 (console) | localhost:9000 (API)"
	@echo "  • Grafana:    http://localhost:3000 (admin/admin)"
	@echo "  • Prometheus: http://localhost:9090"
	@echo ""
	@echo "$(BLUE)🗄️  Databases:$(NC)"
	@docker compose -f $(LOCAL_COMPOSE) ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" | grep -E "db|Database"

dev-down:
	@echo "$(YELLOW)Stopping infrastructure...$(NC)"
	@docker compose -f $(LOCAL_COMPOSE) down
	@echo "$(GREEN)✅ Infrastructure stopped$(NC)"

dev-logs:
	docker compose -f $(LOCAL_COMPOSE) logs -f

dev-ps:
	@docker compose -f $(LOCAL_COMPOSE) ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

dev-clean:
	@echo "$(RED)⚠️  This will delete all local data. Continue? [y/N]$(NC)"
	@read ans && [ $${ans:-N} = y ] && \
		docker compose -f $(LOCAL_COMPOSE) down -v && \
		echo "$(GREEN)✅ Infrastructure cleaned$(NC)"

# ─────────────────────────────────────────────────
# Service Setup & Local Running
# ─────────────────────────────────────────────────

setup:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make setup SERVICE=webhook-service$(NC)"; exit 1; }
	@echo "$(GREEN)📦 Setting up $(SERVICE)...$(NC)"
	@cd services/$(SERVICE) && \
		{ test -f poetry.lock || poetry lock --no-update; } && \
		poetry install --sync
	@if [ -f "services/$(SERVICE)/prisma/schema.prisma" ]; then \
		echo "$(BLUE)Generating Prisma client...$(NC)"; \
		cd services/$(SERVICE) && \
		DATABASE_URL="postgresql://temp:temp@temp:5432/temp" \
		poetry run prisma generate --schema=prisma/schema.prisma; \
	fi
	@echo "$(GREEN)✅ $(SERVICE) setup complete$(NC)"

# Get database connection details for a service
get-db-config:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make get-db-config SERVICE=webhook-service$(NC)"; exit 1; }
	@SERVICE_NAME=$$(echo $(SERVICE) | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); \
	DB_USER=$$(grep "$${SERVICE_NAME}_DB_USER" $(ENV_FILE) | cut -d '=' -f2); \
	DB_PASSWORD=$$(grep "$${SERVICE_NAME}_DB_PASSWORD" $(ENV_FILE) | cut -d '=' -f2); \
	DB_NAME=$$(grep "$${SERVICE_NAME}_DB_NAME" $(ENV_FILE) | cut -d '=' -f2); \
	DB_PORT=$$(grep -E "$${SERVICE_NAME}_DB_(PORT_)?EXTERNAL" $(ENV_FILE) | cut -d '=' -f2); \
	if [ -z "$$DB_USER" ]; then DB_USER=$$(grep "^DB_USER=" $(ENV_FILE) | cut -d '=' -f2); fi; \
	if [ -z "$$DB_PASSWORD" ]; then DB_PASSWORD=$$(grep "^DB_PASSWORD=" $(ENV_FILE) | cut -d '=' -f2); fi; \
	echo "postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}"

run:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make run SERVICE=webhook-service$(NC)"; exit 1; }
	@SERVICE_NAME=$$(echo $(SERVICE) | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); \
	DB_USER=$$(grep "$${SERVICE_NAME}_DB_USER" $(ENV_FILE) | cut -d '=' -f2); \
	DB_PASSWORD=$$(grep "$${SERVICE_NAME}_DB_PASSWORD" $(ENV_FILE) | cut -d '=' -f2); \
	DB_NAME=$$(grep "$${SERVICE_NAME}_DB_NAME" $(ENV_FILE) | cut -d '=' -f2); \
	DB_PORT=$$(grep "$${SERVICE_NAME}_DB_PORT_EXTERNAL" $(ENV_FILE) | cut -d '=' -f2); \
	API_PORT=$$(grep "$${SERVICE_NAME}_API_EXTERNAL_PORT" $(ENV_FILE) | cut -d '=' -f2); \
	echo "$(GREEN)🚀 Starting $(SERVICE) on port $$API_PORT...$(NC)"; \
	cd services/$(SERVICE) && \
		DATABASE_URL="postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}" \
		APP_ENV=local \
		PYTHONPATH="../../shared:../../config" \
		poetry run python -m src.main

run-all:
	@echo "$(GREEN)🚀 Starting all services...$(NC)"
	@trap 'kill 0' SIGINT EXIT; \
	for service_dir in $(SERVICE_DIRS); do \
		SERVICE=$$(basename $$service_dir); \
		($(MAKE) run SERVICE=$$SERVICE 2>&1 | sed "s/^/[$$SERVICE] /") & \
	done; \
	wait

# ─────────────────────────────────────────────────
# Database Management
# ─────────────────────────────────────────────────

db-url:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make db-url SERVICE=webhook-service$(NC)"; exit 1; }
	@DATABASE_URL=$$($(MAKE) -s get-db-config SERVICE=$(SERVICE)); \
	echo "$(BLUE)DATABASE_URL for $(SERVICE):$(NC)"; \
	echo "$$DATABASE_URL"

db-push:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make db-push SERVICE=webhook-service$(NC)"; exit 1; }
	@echo "$(GREEN)📤 Pushing Prisma schema for $(SERVICE)...$(NC)"
	@DATABASE_URL=$$($(MAKE) -s get-db-config SERVICE=$(SERVICE)); \
	cd services/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma db push --schema=prisma/schema.prisma
	@echo "$(GREEN)✅ Schema pushed$(NC)"

db-migrate:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make db-migrate SERVICE=webhook-service NAME='add_user_table'$(NC)"; exit 1; }
	@test -n "$(NAME)" || { echo "$(RED)❌ Please provide migration name: NAME='description'$(NC)"; exit 1; }
	@echo "$(GREEN)🔄 Creating migration for $(SERVICE)...$(NC)"
	@DATABASE_URL=$$($(MAKE) -s get-db-config SERVICE=$(SERVICE)); \
	cd services/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma migrate dev --name $(NAME) --schema=prisma/schema.prisma
	@echo "$(GREEN)✅ Migration created$(NC)"

db-studio:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make db-studio SERVICE=webhook-service$(NC)"; exit 1; }
	@echo "$(GREEN)🎨 Opening Prisma Studio for $(SERVICE)...$(NC)"
	@DATABASE_URL=$$($(MAKE) -s get-db-config SERVICE=$(SERVICE)); \
	cd services/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma studio --schema=prisma/schema.prisma

# ─────────────────────────────────────────────────
# Docker Development (All services in containers)
# ─────────────────────────────────────────────────

docker-dev:
	@echo "$(GREEN)🐳 Starting all services in Docker...$(NC)"
	@docker compose -f $(DEV_COMPOSE) --env-file $(ENV_FILE) up -d
	@echo "$(GREEN)✅ Docker development environment ready$(NC)"

docker-build:
	@echo "$(GREEN)🔨 Building Docker images...$(NC)"
	@docker compose -f $(DEV_COMPOSE) --env-file $(ENV_FILE) build
	@echo "$(GREEN)✅ Build complete$(NC)"

docker-down:
	@docker compose -f $(DEV_COMPOSE) down

docker-logs:
	@docker compose -f $(DEV_COMPOSE) logs -f $(SERVICE)

docker-restart:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make docker-restart SERVICE=webhook-service$(NC)"; exit 1; }
	@docker compose -f $(DEV_COMPOSE) restart $(SERVICE)

# ─────────────────────────────────────────────────
# Production
# ─────────────────────────────────────────────────

prod:
	@echo "$(GREEN)🚀 Starting production environment...$(NC)"
	@docker compose -f $(PROD_COMPOSE) --env-file .env.prod up -d
	@echo "$(GREEN)✅ Production environment ready$(NC)"

prod-build:
	@echo "$(GREEN)🔨 Building production images...$(NC)"
	@docker compose -f $(PROD_COMPOSE) --env-file .env.prod build --no-cache
	@echo "$(GREEN)✅ Production build complete$(NC)"

prod-down:
	@docker compose -f $(PROD_COMPOSE) down

prod-logs:
	@docker compose -f $(PROD_COMPOSE) logs -f $(SERVICE)

prod-clean:
	@echo "$(RED)⚠️  This will delete all production data. Continue? [y/N]$(NC)"
	@read ans && [ $${ans:-N} = y ] && \
		docker compose -f $(PROD_COMPOSE) down -v

# ─────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────

status:
	@echo "$(BLUE)📊 System Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Infrastructure:$(NC)"
	@docker compose -f $(LOCAL_COMPOSE) ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null || echo "  Not running"
	@echo ""
	@echo "$(YELLOW)Local Services:$(NC)"
	@for service in $(SERVICE_NAMES); do \
		if pgrep -f "services/$$service" > /dev/null 2>&1; then \
			echo "  $(GREEN)● $$service (running)$(NC)"; \
		else \
			echo "  ○ $$service (stopped)"; \
		fi; \
	done

clean-all:
	@echo "$(RED)⚠️  This will remove ALL Docker data. Continue? [y/N]$(NC)"
	@read ans && [ $${ans:-N} = y ] && \
		docker system prune -af && \
		docker volume prune -f && \
		echo "$(GREEN)✅ Docker cleaned$(NC)"

list:
	@echo "$(GREEN)📦 Available services:$(NC)"
	@for service in $(SERVICE_NAMES); do \
		if [ -f "services/$$service/prisma/schema.prisma" ]; then \
			echo "  • $$service $(BLUE)[Prisma]$(NC)"; \
		else \
			echo "  • $$service"; \
		fi; \
	done

test:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make test SERVICE=webhook-service$(NC)"; exit 1; }
	@echo "$(GREEN)🧪 Running tests for $(SERVICE)...$(NC)"
	@cd services/$(SERVICE) && poetry run pytest

lint:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make lint SERVICE=webhook-service$(NC)"; exit 1; }
	@echo "$(GREEN)🔍 Linting $(SERVICE)...$(NC)"
	@cd services/$(SERVICE) && \
		poetry run black . && \
		poetry run isort . && \
		poetry run flake8 .

# Quick database connection test
db-test:
	@test -n "$(SERVICE)" || { echo "$(RED)❌ Usage: make db-test SERVICE=webhook-service$(NC)"; exit 1; }
	@DATABASE_URL=$$($(MAKE) -s get-db-config SERVICE=$(SERVICE)); \
	echo "$(BLUE)Testing database connection for $(SERVICE)...$(NC)"; \
	echo "$$DATABASE_URL" | grep -o "postgresql://[^@]*@[^/]*" && \
	docker exec -it $$(echo $(SERVICE) | sed 's/-service/-db-local/') pg_isready 2>/dev/null && \
	echo "$(GREEN)✅ Database is reachable$(NC)" || \
	echo "$(RED)❌ Database is not reachable$(NC)"