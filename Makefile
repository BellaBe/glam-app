# ──────────────────────────────────────────────
# Makefile – Dev & Prod helpers (Fashion stack)
# ──────────────────────────────────────────────

# Adjust if you rename folders
SERVICE_DIRS = \
	services/selfie \
	services/cv_cloth \
	services/vlm_service \
	services/recommendation \
	services/narrator_llm \
	services/api_gateway


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

dev: ## Up infra containers only
	docker compose -f $(LOCAL_COMPOSE) up -d

dev-down: ## Stop infra containers
	docker compose -f $(LOCAL_COMPOSE) down

dev-logs: ## Follow logs
	docker compose -f $(LOCAL_COMPOSE) logs -f

dev-ps: ## List containers
	docker compose -f $(LOCAL_COMPOSE) ps

dev-clean: ## Remove infra containers & volumes
	docker compose -f $(LOCAL_COMPOSE) down -v
	
# ---------- Per-service helpers ----------
install-service: ## SERVICE=<folder>  – Poetry install only that service
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make install-service SERVICE=selfie"; exit 1; fi
	cd services/$(SERVICE) && poetry install

download-models: ## fetch antelopev2 once
	mkdir -p services/selfies/models
	curl -L https://github.com/deepinsight/insightface/releases/download/v0.7/antelopev2.zip \
	     -o services/selfies/models/antelopev2.zip
	unzip -oq services/selfies/models/antelopev2.zip -d services/selfies/models
	rm services/selfies/models/antelopev2.zip
	
download-cloth-models:  ## fetch MP cloth-seg TFLite
	@mkdir -p services/cloths/models
	curl -L https://storage.googleapis.com/mediapipe-assets/selfie_multiclass_256x256.tflite \
	     -o services/cloths/models/selfie_multiclass_256x256.tflite


# Run one service with hot-reload: make run-service SERVICE=selfie
run-service: ## SERVICE=<folder>
	@if [ -z "$(SERVICE)" ]; then \
	  echo "Usage: make run-service SERVICE=selfie"; exit 1; fi
	cd services/$(SERVICE) && \
	pip install -e ../../shared && \
	PYTHONPATH=../../shared poetry run uvicorn src.main:app \
		--reload --host 0.0.0.0 --port 8000

# Run ALL services locally with hot-reload (Ctrl-C to kill)
run-all-services: ## Run every service locally
	@trap 'kill 0' SIGINT EXIT; \
	for d in $(SERVICE_DIRS); do \
	  ( cd $$d && \
	    pip install -e ../../shared && \
	    PYTHONPATH=../../shared poetry run uvicorn src.main:app \
	      --reload --host 0.0.0.0 --port 0 ) & \
	done; \
	wait

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



# # Initialize Alembic (run once)
# poetry run alembic init alembic

# # Create a new migration
# poetry run alembic revision --autogenerate -m "Create selfie analysis tables"

# # Apply migrations
# poetry run alembic upgrade head

# # Downgrade migrations  
# poetry run alembic downgrade -1

# # Seed database
# poetry run seed-db

# # Setup ML models
# poetry run setup-ml