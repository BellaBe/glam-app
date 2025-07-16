# ──────────────────────────────────────────────
# Makefile – Dev & Prod helpers (Fashion stack)
# ──────────────────────────────────────────────

# Adjust if you rename folders
SERVICE_DIRS = \
	services/catalog-ai-apparel \
	services/catalog-connector \
	services/catalog-image-cache \
	services/catalog-job-processor \
	services/catalog-service \
	services/profile-service \
	services/profile-ai-selfie

# Compose files
LOCAL_COMPOSE = docker-compose.local.yml
PROD_COMPOSE  = docker-compose.yml

.PHONY: help install dev dev-down dev-logs dev-ps dev-clean \
        prod prod-build prod-down prod-logs prod-ps prod-clean \
        run-service run-all-services clean-dev clean-prod clean-all \
        docker-health docker-size

# ---------- General ----------

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Poetry install every service locally
	@for d in $(SERVICE_DIRS); do \
	  echo "→ Installing deps in $$d"; \
	  cd $$d && poetry install; \
	done

# ---------- Local dev (infra in docker) ----------

dev: ## Start all infrastructure including monitoring
	@echo "🚀 Starting development infrastructure..."
	docker compose -f $(LOCAL_COMPOSE) up -d
	@echo "⏳ Waiting for services to initialize..."
	@sleep 5
	@echo "✅ Infrastructure started!"
	@echo ""
	@echo "📊 Services available at:"
	@echo "   • NATS:       http://localhost:4222 (clients), http://localhost:8222 (monitoring)"
	@echo "   • Redis:      localhost:6379"
	@echo "   • MailHog:    http://localhost:8025 (UI), localhost:1025 (SMTP)"
	@echo "   • MinIO:      http://localhost:9001 (console), localhost:9000 (API)"
	@echo "   • Databases:  See .env for ports"
	@echo ""
	@echo "📈 Monitoring available at:"
	@echo "   • Grafana:    http://localhost:3000 (admin/admin)"
	@echo "   • Prometheus: http://localhost:9090"
	@echo "   • Metrics:    http://localhost:7777/metrics (NATS)"
	@echo "                 http://localhost:9121/metrics (Redis)"

dev-core: ## Start only core services (no monitoring)
	@echo "Starting core infrastructure only..."
	docker compose -f $(LOCAL_COMPOSE) up -d nats redis mailhog minio minio-setup catalog-db notification-db profile-db catalog-job-processor-db

dev-monitoring: ## Start only monitoring stack
	@echo "Starting monitoring stack..."
	docker compose -f $(LOCAL_COMPOSE) up -d prometheus grafana nats-exporter redis-exporter
	@echo "Monitoring services starting at:"
	@echo "   • Grafana:    http://localhost:3000"
	@echo "   • Prometheus: http://localhost:9090"

dev-down: ## Stop all infrastructure
	docker compose -f $(LOCAL_COMPOSE) down

dev-logs: ## Follow logs (all services)
	docker compose -f $(LOCAL_COMPOSE) logs -f

dev-logs-app: ## Follow logs (app services only)
	docker compose -f $(LOCAL_COMPOSE) logs -f nats redis mailhog

dev-logs-monitoring: ## Follow logs (monitoring only)
	docker compose -f $(LOCAL_COMPOSE) logs -f prometheus grafana nats-exporter redis-exporter

dev-ps: ## List containers
	docker compose -f $(LOCAL_COMPOSE) ps

dev-health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@docker compose -f $(LOCAL_COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

dev-clean: ## Remove all containers & volumes (WARNING: deletes data)
	@echo "⚠️  This will delete all local data. Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	docker compose -f $(LOCAL_COMPOSE) down -v
	@echo "🧹 Cleanup complete"

dev-restart: ## Restart all services
	@make dev-down
	@make dev

dev-reset-monitoring: ## Reset monitoring data only
	docker compose -f $(LOCAL_COMPOSE) stop prometheus grafana
	docker volume rm -f $(shell docker volume ls -q | grep -E "(prometheus|grafana)-data")
	docker compose -f $(LOCAL_COMPOSE) up -d prometheus grafana
	@echo "Monitoring data reset"

# ---------- Shortcuts ----------
up: dev ## Alias for 'make dev'
down: dev-down ## Alias for 'make dev-down'
logs: dev-logs ## Alias for 'make dev-logs'
ps: dev-ps ## Alias for 'make dev-ps'

# ---------- Per-service helpers ----------
install-service: ## SERVICE=<folder>  – Poetry install only that service
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make install-service SERVICE=<folder>"; exit 1; fi
	cd services/$(SERVICE) && poetry install

download-models: ## fetch antelopev2 once
	mkdir -p services/catalog-ai-apparel/models
	curl -L https://github.com/deepinsight/insightface/releases/download/v0.7/antelopev2.zip \
	     -o services/catalog-ai-apparel/models/antelopev2.zip
	unzip -oq services/catalog-ai-apparel/models/antelopev2.zip -d services/catalog-ai-apparel/models
	rm services/catalog-ai-apparel/models/antelopev2.zip

download-cloth-models:  ## fetch MP cloth-seg TFLite
	@mkdir -p services/catalog-connector/models
	curl -L https://storage.googleapis.com/mediapipe-assets/selfie_multiclass_256x256.tflite \
	     -o services/catalog-connector/models/selfie_multiclass_256x256.tflite

download-selfie-models: ## fetch antelopev2 for profile-ai-selfie
	mkdir -p services/profile-ai-selfie/models
	curl -L https://github.com/deepinsight/insightface/releases/download/v0.7/antelopev2.zip \
	     -o services/profile-ai-selfie/models/antelopev2.zip
	unzip -oq services/profile-ai-selfie/models/antelopev2.zip -d services/profile-ai-selfie/models
	rm services/profile-ai-selfie/models/antelopev2.zip

download-all-models: download-models download-cloth-models download-selfie-models ## fetch all AI models

# Run one FASTApiservice with hot-reload: make run-service SERVICE=catalog-service
# Usage: make run SERVICE=catalog-service PORT=8000
run-service:
	@if [ -z "$(SERVICE)" ]; then \
	  echo "❌ Usage: make run-service SERVICE=notification-service"; \
	  exit 1; \
	fi
	@echo "🚀 Running service: $(SERVICE)"
	
	# Check if service directory exists
	@if [ ! -d "services/$(SERVICE)" ]; then \
	  echo "❌ Service directory not found: services/$(SERVICE)"; \
	  exit 1; \
	fi
	
	# Install shared package
	@echo "📦 Installing shared package..."
	@cd services/$(SERVICE) && pip install -e ../../shared
	
	# NO PORT EXTRACTION - service handles its own port via effective_port!
	@echo "🎯 Starting $(SERVICE) (port determined by service config)..."
	@cd services/$(SERVICE) && \
	PYTHONPATH=../../shared:../../config poetry run python -m src.main --reload --host 0.0.0.0

		
# Run one non-FASTAPI service (e.g. catalog-job-processor) with hot-reload
run-non-fastapi-service: ## SERVICE=<folder>
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make run-non-fastapi-service SERVICE=catalog-job-processor"; exit 1; fi
	cd services/$(SERVICE) && \
	pip install -e ../../shared && \
	PYTHONPATH=../../shared poetry run -m python src.main

# Run ALL services locally with hot-reload (Ctrl-C to kill)

clean_env: ## Remove all .env files in services
	unset $(env | grep ^NOTIFICATION_ | cut -d= -f1) ## Unset all notification service env vars

# ---------- Production (everything in docker) ----------

prod: ## docker-compose up -d
	docker compose -f $(PROD_COMPOSE) up -d

prod-build: ## Build images
	docker compose -f $(PROD_COMPOSE) build

prod-down: ## Stop prod stack
	docker compose -f $(PROD_COMPOSE) down

prod-logs: ## Logs
	docker compose -f $(PROD_COMPOSE) logs -f

prod-ps: ## ps
	docker compose -f $(PROD_COMPOSE) ps

prod-clean: ## Down + volumes
	docker compose -f $(PROD_COMPOSE) down -v

# ---------- Profile Service Specific Commands ----------

run-profile-service: ## Run profile service locally
	cd services/profile-service && \
	pip install -e ../../shared && \
	PYTHONPATH=../../shared poetry run uvicorn src.main:app \
		--reload --host 0.0.0.0 --port 8007

run-profile-ai: ## Run profile AI selfie worker locally
	cd services/profile-ai-selfie && \
	pip install -e ../../shared && \
	PYTHONPATH=../../shared poetry run python src.main

test-profile-upload: ## Test selfie upload endpoint
	@echo "Testing profile service health..."
	@curl -s http://localhost:8007/health | jq .
	@echo "\nTesting selfie upload (requires running service)..."
	@echo "Run: curl -X POST -F 'file=@test.jpg' -F 'persist=false' http://localhost:8007/api/v1/selfies/upload"

# ---------- Database Helpers ----------

db-migrate-profile: ## Run profile database migrations
	cd services/profile-service && \
	poetry run alembic upgrade head

db-connect-profile: ## Connect to profile database
	docker exec -it profile-db psql -U $(PROFILE_DB_USER) -d $(PROFILE_DB_NAME)

# ---------- Docker housekeeping ----------

clean-dev: ## stop dev + prune
	docker compose -f $(LOCAL_COMPOSE) down -v
	docker system prune -af --filter "until=24h"
	docker volume prune -f

clean-prod: ## stop prod + prune
	docker compose -f $(PROD_COMPOSE) down -v
	docker system prune -af --filter "until=24h"
	docker volume prune -f

clean-all: ## nuke everything
	docker system prune -af
	docker volume prune -f

docker-health: ## show container health & ports
	@docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

docker-size: ## disk usage
	docker system df

# ---------- Development Shortcuts ----------

dev-profile: ## Start only profile-related services
	docker compose -f $(PROD_COMPOSE) up -d nats redis profile-db
	@echo "Infrastructure ready. Run 'make run-profile-service' and 'make run-profile-ai'"

prod-profile: ## Build and start profile services in Docker
	docker compose -f $(PROD_COMPOSE) build profile-service profile-ai-selfie
	docker compose -f $(PROD_COMPOSE) up -d profile-db profile-service profile-ai-selfie

logs-profile: ## Show logs for profile services
	docker compose -f $(PROD_COMPOSE) logs -f profile-service profile-ai-selfie

# ---------- Monitoring ----------

check-services: ## Check all service health endpoints
	@echo "Checking service health..."
	@echo "Catalog Service: " && curl -s http://localhost:8001/health 2>/dev/null || echo "DOWN"
	@echo "Profile Service: " && curl -s http://localhost:8007/health 2>/dev/null || echo "DOWN"
	@echo "\nNATS: " && curl -s http://localhost:8222/varz 2>/dev/null | jq -r '.server_name' || echo "DOWN"
	@echo "Redis: " && docker exec glam-redis redis-cli ping 2>/dev/null || echo "DOWN"