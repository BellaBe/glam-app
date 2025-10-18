# Makefile
.DEFAULT_GOAL := help

# Compose command shortcuts
DC_LOCAL = docker compose -f infrastructure/docker-compose.yml -f infrastructure/docker-compose.local.yml --env-file infrastructure/.env.local
DC_DEV = docker compose -f infrastructure/docker-compose.yml -f infrastructure/docker-compose.dev.yml --env-file infrastructure/.env.dev
DC_PROD = docker compose -f infrastructure/docker-compose.yml -f infrastructure/docker-compose.prod.yml --env-file infrastructure/.env.prod

# Service lists
INFRA_SERVICES = postgres nats
API_SERVICES = analytics-service billing-service catalog-service catalog-connector credit-service merchant-service notification-service recommendation-service season-compatibility-service selfie-service token-service webhook-service
AI_SERVICES = selfie-ai-analyzer catalog-ai-analyzer
ALL_SERVICES = $(INFRA_SERVICES) $(API_SERVICES) $(AI_SERVICES)

# Port mappings for local development
PORT_analytics-service = 8001
PORT_billing-service = 8002
PORT_catalog-service = 8003
PORT_catalog-connector = 8004
PORT_credit-service = 8005
PORT_merchant-service = 8006
PORT_notification-service = 8007
PORT_recommendation-service = 8008
PORT_season-compatibility-service = 8009
PORT_selfie-service = 8010
PORT_token-service = 8011
PORT_webhook-service = 8012
PORT_selfie-ai-analyzer = 8013
PORT_catalog-ai-analyzer = 8014

##@ Local (Infrastructure Only + Run Services on Host)

local: ## Start local infrastructure (Postgres, NATS, MailHog)
	$(DC_LOCAL) up -d postgres nats mailhog
	@echo "\n✅ Local infrastructure ready:"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  NATS: localhost:4222"
	@echo "  NATS Monitor: http://localhost:8222"
	@echo "  MailHog UI: http://localhost:8025"
	@echo "  SMTP: localhost:1025"
	@echo "\n💡 Run services with: make run-<service-name>"
	@echo "   Examples:"
	@echo "     make run-notification"
	@echo "     make run-analytics"
	@echo "     make run-token"

local-stop: ## Stop local infrastructure
	$(DC_LOCAL) down

local-logs: ## Show local logs
	$(DC_LOCAL) logs -f $(ARGS)

local-clean: ## Clean local (with volumes)
	$(DC_LOCAL) down -v
	@echo "✅ Local cleanup complete"

local-ps: ## Show local status
	$(DC_LOCAL) ps

local-restart: ## Restart local infrastructure
	$(DC_LOCAL) restart $(ARGS)

##@ Run Services Locally (on host with Poetry)

# Add database URL construction helper
define get_db_url
postgresql+asyncpg://postgres:postgres@localhost:5432/$(1)
endef

run-service: ## Run service locally (internal use, see run-<service> targets)
	@if [ -z "$(SERVICE)" ]; then \
		echo "❌ SERVICE not specified"; \
		exit 1; \
	fi
	@if [ ! -d "services/$(SERVICE)" ]; then \
		echo "❌ Service not found: services/$(SERVICE)"; \
		exit 1; \
	fi
	@PORT=$${PORT:-8000}; \
	DB_NAME=$${DB_NAME:-}; \
	if [ -n "$$DB_NAME" ]; then \
		export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/$$DB_NAME"; \
	fi; \
	export APP_ENV=local; \
	export NATS_URL=nats://localhost:4222; \
	echo "🚀 Starting $(SERVICE) on port $$PORT..."; \
	if [ -n "$$DB_NAME" ]; then \
		echo "📊 Database: $$DB_NAME"; \
	fi; \
	echo "📝 Logs will appear below. Press Ctrl+C to stop."; \
	echo ""; \
	cd services/$(SERVICE) && \
	if [ ! -d ".venv" ]; then \
		echo "📦 Installing dependencies..."; \
		poetry install; \
	fi && \
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port $$PORT

run-analytics: ## Run analytics-service (port 8001)
	@make run-service SERVICE=analytics-service PORT=8001 DB_NAME=analytics_db

run-billing: ## Run billing-service (port 8002)
	@make run-service SERVICE=billing-service PORT=8002 DB_NAME=billing_db

run-catalog: ## Run catalog-service (port 8003)
	@make run-service SERVICE=catalog-service PORT=8003 DB_NAME=catalog_db

run-catalog-connector: ## Run catalog-connector (port 8004)
	@make run-service SERVICE=catalog-connector PORT=8004

run-credit: ## Run credit-service (port 8005)
	@make run-service SERVICE=credit-service PORT=8005 DB_NAME=credit_db

run-merchant: ## Run merchant-service (port 8006)
	@make run-service SERVICE=merchant-service PORT=8006 DB_NAME=merchant_db

run-notification: ## Run notification-service (port 8007)
	@make run-service SERVICE=notification-service PORT=8007 DB_NAME=notification_db

run-recommendation: ## Run recommendation-service (port 8008)
	@make run-service SERVICE=recommendation-service PORT=8008 DB_NAME=recommendation_db

run-season: ## Run season-compatibility-service (port 8009)
	@make run-service SERVICE=season-compatibility-service PORT=8009 DB_NAME=season_compatibility_db

run-selfie: ## Run selfie-service (port 8010)
	@make run-service SERVICE=selfie-service PORT=8010 DB_NAME=selfie_db

run-token: ## Run token-service (port 8011)
	@make run-service SERVICE=token-service PORT=8011 DB_NAME=token_db

run-webhook: ## Run webhook-service (port 8012)
	@make run-service SERVICE=webhook-service PORT=8012 DB_NAME=webhook_db

run-selfie-ai: ## Run selfie-ai-analyzer (port 8013)
	@make run-service SERVICE=selfie-ai-analyzer PORT=8013

run-catalog-ai: ## Run catalog-ai-analyzer (port 8014)
	@make run-service SERVICE=catalog-ai-analyzer PORT=8014

##@ Local Service Management

migrate-service: ## Run migrations for a service (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make migrate-service SERVICE=notification-service"; \
		exit 1; \
	fi
	@if [ ! -d "services/$(SERVICE)/alembic" ]; then \
		echo "⚠️  No alembic directory found in services/$(SERVICE)"; \
		exit 1; \
	fi
	@echo "🔄 Running migrations for $(SERVICE)..."
	cd services/$(SERVICE) && poetry run alembic upgrade head
	@echo "✅ Migrations complete"

install-service: ## Install service dependencies (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make install-service SERVICE=notification-service"; \
		exit 1; \
	fi
	@echo "📦 Installing dependencies for $(SERVICE)..."
	cd services/$(SERVICE) && poetry install
	@echo "✅ Dependencies installed"

shell-service: ## Open poetry shell for service (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make shell-service SERVICE=notification-service"; \
		exit 1; \
	fi
	cd services/$(SERVICE) && poetry shell

test-service: ## Run tests for service (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make test-service SERVICE=notification-service"; \
		exit 1; \
	fi
	@echo "🧪 Running tests for $(SERVICE)..."
	cd services/$(SERVICE) && poetry run pytest

lint-service: ## Lint service code (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make lint-service SERVICE=notification-service"; \
		exit 1; \
	fi
	@echo "🔍 Linting $(SERVICE)..."
	cd services/$(SERVICE) && poetry run ruff check .

format-service: ## Format service code (use SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make format-service SERVICE=notification-service"; \
		exit 1; \
	fi
	@echo "✨ Formatting $(SERVICE)..."
	cd services/$(SERVICE) && poetry run ruff format .

##@ Development (Full Stack in Docker)

dev: ## Start dev (full stack with hot reload)
	@echo "🚀 Starting dev environment..."
	$(DC_DEV) up -d postgres nats mailhog
	@echo "⏳ Waiting for infrastructure (30s)..."
	@sleep 30
	@echo "🔨 Building and starting services..."
	$(DC_DEV) up -d --build $(API_SERVICES)
	@sleep 20
	$(DC_DEV) up -d --build $(AI_SERVICES)
	@sleep 10
	$(DC_DEV) up -d caddy
	@echo "\n✅ Dev environment ready!"
	@echo "  API Gateway: http://localhost"
	@echo "  Services: http://localhost:8001-8014"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  NATS: localhost:4222"
	@echo "  MailHog: http://localhost:8025"
	@echo "\n💡 Use 'make dev-logs' to watch logs"

dev-quick: ## Start dev without rebuild
	$(DC_DEV) up -d

dev-stop: ## Stop dev
	$(DC_DEV) down

dev-restart: ## Restart dev services
	$(DC_DEV) restart $(ARGS)

dev-logs: ## Show dev logs (use ARGS=service-name for specific service)
	$(DC_DEV) logs -f $(ARGS)

dev-ps: ## Show dev status
	$(DC_DEV) ps

dev-stats: ## Show resource usage
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

dev-clean: ## Clean dev (with volumes)
	$(DC_DEV) down -v
	@echo "✅ Dev cleanup complete"

dev-rebuild: ## Rebuild and restart dev
	$(DC_DEV) up -d --build --force-recreate $(ARGS)

dev-shell: ## Shell into dev service (use ARGS=service-name)
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make dev-shell ARGS=service-name"; \
		exit 1; \
	fi
	$(DC_DEV) exec $(ARGS) /bin/sh

##@ Production

prod-build: ## Build production images
	@echo "🔨 Building production images..."
	$(DC_PROD) build --parallel

prod-up: ## Start production (staged rollout)
	@echo "🚀 Starting production environment..."
	@echo "⏳ Step 1/5: Infrastructure..."
	$(DC_PROD) up -d postgres nats
	@sleep 30
	@echo "⏳ Step 2/5: Core services..."
	$(DC_PROD) up -d token-service billing-service credit-service merchant-service
	@sleep 30
	@echo "⏳ Step 3/5: Supporting services..."
	$(DC_PROD) up -d webhook-service notification-service analytics-service
	@sleep 30
	@echo "⏳ Step 4/5: AI services..."
	$(DC_PROD) up -d selfie-ai-analyzer catalog-ai-analyzer
	@sleep 30
	@echo "⏳ Step 5/5: Application services + Gateway..."
	$(DC_PROD) up -d selfie-service season-compatibility-service catalog-service recommendation-service catalog-connector
	@sleep 20
	$(DC_PROD) up -d caddy
	@echo "\n✅ Production deployed!"
	@make prod-health

prod-quick: ## Start production without staged rollout
	$(DC_PROD) up -d

prod-down: ## Stop production
	$(DC_PROD) down

prod-restart: ## Restart production service (use ARGS=service-name)
	$(DC_PROD) restart $(ARGS)

prod-logs: ## Show production logs (use ARGS=service-name)
	$(DC_PROD) logs -f $(ARGS)

prod-ps: ## Show production status
	$(DC_PROD) ps

prod-stats: ## Show production resource usage
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"

prod-health: ## Check production health
	@echo "\n🏥 Health Check:"
	@for service in $(API_SERVICES) $(AI_SERVICES); do \
		status=$$(docker inspect -f '{{.State.Health.Status}}' infrastructure-$$service-1 2>/dev/null || echo "not running"); \
		if [ "$$status" = "healthy" ]; then \
			echo "  ✅ $$service"; \
		elif [ "$$status" = "not running" ]; then \
			echo "  ⚫ $$service (not running)"; \
		else \
			echo "  ⚠️  $$service ($$status)"; \
		fi; \
	done

prod-pull: ## Pull production images
	$(DC_PROD) pull

prod-update: ## Update production (pull + restart)
	@echo "🔄 Updating production..."
	$(DC_PROD) pull
	$(DC_PROD) up -d --no-deps $(ARGS)
	@echo "✅ Update complete"

prod-rollback: ## Rollback production (use TAG=previous-tag)
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make prod-rollback TAG=previous-tag"; \
		exit 1; \
	fi
	@echo "🔙 Rolling back to $(TAG)..."
	TAG=$(TAG) $(DC_PROD) up -d --no-deps $(ARGS)

##@ Database

db-shell: ## PostgreSQL shell (ENV=local|dev|prod, default=local)
	@if [ "$(ENV)" = "prod" ]; then \
		$(DC_PROD) exec postgres psql -U postgres; \
	elif [ "$(ENV)" = "dev" ]; then \
		$(DC_DEV) exec postgres psql -U postgres; \
	else \
		$(DC_LOCAL) exec postgres psql -U postgres; \
	fi

db-backup: ## Backup databases (ENV=local|dev|prod, default=local)
	@mkdir -p backups
	@ENV_NAME=$${ENV:-local}; \
	TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	if [ "$$ENV_NAME" = "prod" ]; then \
		$(DC_PROD) exec postgres pg_dumpall -U postgres > backups/prod_$$TIMESTAMP.sql; \
	elif [ "$$ENV_NAME" = "dev" ]; then \
		$(DC_DEV) exec postgres pg_dumpall -U postgres > backups/dev_$$TIMESTAMP.sql; \
	else \
		$(DC_LOCAL) exec postgres pg_dumpall -U postgres > backups/local_$$TIMESTAMP.sql; \
	fi
	@echo "✅ Backup complete: backups/$$ENV_NAME_$$TIMESTAMP.sql"

db-restore: ## Restore database (ENV=local|dev|prod FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make db-restore ENV=local FILE=backups/local_20240101_120000.sql"; \
		exit 1; \
	fi
	@echo "⚠️  This will overwrite the current database!"
	@read -p "Continue? (yes/NO): " confirm; \
	if [ "$$confirm" != "yes" ]; then exit 1; fi
	@if [ "$(ENV)" = "prod" ]; then \
		cat $(FILE) | $(DC_PROD) exec -T postgres psql -U postgres; \
	elif [ "$(ENV)" = "dev" ]; then \
		cat $(FILE) | $(DC_DEV) exec -T postgres psql -U postgres; \
	else \
		cat $(FILE) | $(DC_LOCAL) exec -T postgres psql -U postgres; \
	fi
	@echo "✅ Restore complete"

db-stats: ## Show database statistics (ENV=local|dev|prod, default=local)
	@if [ "$(ENV)" = "prod" ]; then \
		$(DC_PROD) exec postgres psql -U postgres -c "SELECT * FROM db_sizes;" -c "SELECT * FROM db_connections;"; \
	elif [ "$(ENV)" = "dev" ]; then \
		$(DC_DEV) exec postgres psql -U postgres -c "SELECT * FROM db_sizes;" -c "SELECT * FROM db_connections;"; \
	else \
		$(DC_LOCAL) exec postgres psql -U postgres -c "SELECT * FROM db_sizes;" -c "SELECT * FROM db_connections;"; \
	fi

db-migrate-all: ## Run migrations for all services (ENV=local only)
	@echo "🔄 Running migrations for all services..."
	@for service in $(API_SERVICES); do \
		if [ -d "services/$$service/alembic" ]; then \
			echo "  Migrating $$service..."; \
			cd services/$$service && poetry run alembic upgrade head && cd ../..; \
		fi; \
	done
	@echo "✅ All migrations complete"

##@ Debugging

debug: ## Debug container (use ARGS=service-name)
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make debug ARGS=service-name"; \
		exit 1; \
	fi
	@bash infrastructure/scripts/debug-container.sh $(ARGS)

logs-error: ## Show only error logs (ENV=local|dev|prod)
	@if [ "$(ENV)" = "prod" ]; then \
		$(DC_PROD) logs --tail=100 | grep -i error; \
	elif [ "$(ENV)" = "dev" ]; then \
		$(DC_DEV) logs --tail=100 | grep -i error; \
	else \
		$(DC_LOCAL) logs --tail=100 | grep -i error; \
	fi

logs-service: ## Follow specific service logs (ENV=local|dev|prod SERVICE=service-name)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make logs-service ENV=dev SERVICE=analytics-service"; \
		exit 1; \
	fi
	@if [ "$(ENV)" = "prod" ]; then \
		$(DC_PROD) logs -f $(SERVICE); \
	elif [ "$(ENV)" = "dev" ]; then \
		$(DC_DEV) logs -f $(SERVICE); \
	else \
		$(DC_LOCAL) logs -f $(SERVICE); \
	fi

inspect: ## Inspect container (use ARGS=service-name)
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make inspect ARGS=service-name"; \
		exit 1; \
	fi
	@docker inspect $(ARGS) | jq '.[0] | {State, Health, NetworkSettings: {Networks}, Config: {Env}}'

##@ Utilities

validate: ## Validate all compose files
	@echo "🔍 Validating configurations..."
	@$(DC_LOCAL) config > /dev/null && echo "  ✅ Local"
	@$(DC_DEV) config > /dev/null && echo "  ✅ Dev"
	@$(DC_PROD) config > /dev/null && echo "  ✅ Prod"
	@echo "✅ All configurations valid"

install-all: ## Install dependencies for all services
	@echo "📦 Installing dependencies for all services..."
	@for service in $(API_SERVICES) $(AI_SERVICES); do \
		if [ -d "services/$$service" ]; then \
			echo "  Installing $$service..."; \
			cd services/$$service && poetry install && cd ../..; \
		fi; \
	done
	@echo "✅ All dependencies installed"

clean-logs: ## Clean all container logs
	@echo "🧹 Cleaning container logs..."
	@for container in $$(docker ps -aq); do \
		log_path=$$(docker inspect --format='{{.LogPath}}' $$container 2>/dev/null); \
		if [ -n "$$log_path" ] && [ -f "$$log_path" ]; then \
			echo "Truncating $$log_path"; \
			truncate -s 0 $$log_path; \
		fi; \
	done
	@echo "✅ Logs cleaned"

clean-images: ## Remove unused images
	@echo "🧹 Cleaning unused images..."
	docker image prune -af
	@echo "✅ Images cleaned"

clean-volumes: ## Remove unused volumes (DANGEROUS)
	@echo "⚠️  This will remove ALL unused volumes!"
	@read -p "Continue? (yes/NO): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker volume prune -f; \
		echo "✅ Volumes cleaned"; \
	fi

clean-all: ## Nuclear option - remove everything
	@echo "⚠️  This will remove ALL Docker resources!"
	@echo "⚠️  All data will be lost!"
	@sleep 3
	@read -p "Type 'DELETE EVERYTHING' to confirm: " confirm; \
	if [ "$$confirm" = "DELETE EVERYTHING" ]; then \
		$(DC_LOCAL) down -v 2>/dev/null || true; \
		$(DC_DEV) down -v 2>/dev/null || true; \
		$(DC_PROD) down -v 2>/dev/null || true; \
		docker system prune -af --volumes; \
		echo "✅ Everything cleaned"; \
	else \
		echo "Aborted"; \
	fi

ps-all: ## Show all running containers
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

disk-usage: ## Show Docker disk usage
	@docker system df -v

security-scan: ## Run security scan on images (requires docker scout)
	@if ! command -v docker scout >/dev/null 2>&1; then \
		echo "❌ docker scout not installed"; \
		exit 1; \
	fi
	@bash infrastructure/scripts/security-scan.sh

version: ## Show versions
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker compose version)"
	@echo "Make: $$(make --version | head -1)"
	@echo "Poetry: $$(poetry --version 2>/dev/null || echo 'not installed')"

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1m🚀 GlamYouUp Infrastructure\033[0m\n\nUsage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo "\n\033[1mCommon Workflows:\033[0m"
	@echo "  \033[33mLocal Development (recommended):\033[0m"
	@echo "    make local                    # Start infra"
	@echo "    make run-notification         # Run service with hot reload"
	@echo "    make run-analytics            # Run another service"
	@echo ""
	@echo "  \033[33mFull Dev Stack (Docker):\033[0m"
	@echo "    make dev                      # Start everything in Docker"
	@echo "    make dev-logs ARGS=notification-service"
	@echo ""
	@echo "  \033[33mProduction:\033[0m"
	@echo "    make prod-build               # Build images"
	@echo "    make prod-up                  # Deploy with staged rollout"
	@echo "    make prod-health              # Check status"
	@echo ""
	@echo "  \033[33mDatabase:\033[0m"
	@echo "    make db-shell ENV=local"
	@echo "    make migrate-service SERVICE=notification-service"
	@echo "    make db-backup ENV=prod"
	@echo ""

.PHONY: help local local-stop local-logs local-clean local-ps local-restart \
        run-service run-analytics run-billing run-catalog run-catalog-connector run-credit \
        run-merchant run-notification run-recommendation run-season run-selfie run-token \
        run-webhook run-selfie-ai run-catalog-ai \
        migrate-service install-service shell-service test-service lint-service format-service \
        dev dev-quick dev-stop dev-restart dev-logs dev-ps dev-stats dev-clean dev-rebuild dev-shell \
        prod-build prod-up prod-quick prod-down prod-restart prod-logs prod-ps prod-stats prod-health prod-pull prod-update prod-rollback \
        db-shell db-backup db-restore db-stats db-migrate-all \
        debug logs-error logs-service inspect \
        validate install-all clean-logs clean-images clean-volumes clean-all ps-all disk-usage security-scan version
