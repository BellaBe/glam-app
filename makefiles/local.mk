# ================================================================
# LOCAL DEVELOPMENT - Infrastructure in Docker, Services on Host
# ================================================================

.PHONY: local
local: local-infra ## Start local development environment
	@$(call print_success,"Local infrastructure is running!")
	@echo ""
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  1. Setup a service:  $(BOLD)make local-setup SERVICE=webhook-service$(RESET)"
	@echo "  2. Run a service:    $(BOLD)make local-run SERVICE=webhook-service$(RESET)"
	@echo "  3. Run all services: $(BOLD)make local-run-all$(RESET)"

.PHONY: local-infra
local-infra: ## Start local infrastructure (postgres, nats, minio)
	@$(call print_info,"Starting local infrastructure...")
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local up -d
	@$(MAKE) local-wait
	@$(MAKE) local-infra-status

.PHONY: local-stop
local-stop: ## Stop local infrastructure
	@$(call print_info,"Stopping local infrastructure...")
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local stop

.PHONY: local-down
local-down: ## Stop and remove local infrastructure
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local down

.PHONY: local-clean
local-clean: ## Clean local environment (removes data)
	@$(call confirm,"This will delete all local data")
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local down -v

.PHONY: local-logs
local-logs: ## Show local infrastructure logs
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local logs -f

.PHONY: local-infra-status
local-infra-status: ## Show infrastructure status
	@echo "$(CYAN)Infrastructure Status:$(RESET)"
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

.PHONY: local-setup
local-setup: ## Setup a service for local development
	@$(call check_service,"local-setup")
	@$(call print_info,"Setting up $(SERVICE)...")
	@cd $(SERVICES_DIR)/$(SERVICE) && \
		poetry install --sync && \
		if [ -f prisma/schema.prisma ]; then \
			$(call print_info,"Generating Prisma client...") && \
			poetry run prisma generate; \
		fi
	@$(call print_success,"$(SERVICE) setup complete")

.PHONY: local-run
local-run: ## Run a service locally
	@test -n "$(SERVICE)" || { echo "Usage: make local-run SERVICE=notification-service"; exit 1; }; SERVICE_NAME=$$(echo $(SERVICE) | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); DB_USER=$$(grep "$${SERVICE_NAME}_DB_USER" .env | cut -d '=' -f2); DB_PASSWORD=$$(grep "$${SERVICE_NAME}_DB_PASSWORD" .env | cut -d '=' -f2); DB_NAME=$$(grep "$${SERVICE_NAME}_DB_NAME" .env | cut -d '=' -f2); DB_PORT=$$(grep "$${SERVICE_NAME}_DB_PORT_EXTERNAL" .env | cut -d '=' -f2); cd services/$(SERVICE) && DATABASE_URL="postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}" APP_ENV=local poetry run python -m src.main

.PHONY: local-run-all
local-run-all: ## Run all services locally
	@$(call print_header,"Starting All Services Locally")
	@trap 'kill 0' SIGINT EXIT; \
	for service in $(SERVICE_NAMES); do \
		($(MAKE) local-run SERVICE=$$service 2>&1 | sed "s/^/[$$service] /") & \
	done; \
	wait

.PHONY: local-status
local-status: ## Show local environment status
	@echo "$(CYAN)$(BOLD)LOCAL Environment:$(RESET)"
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null || echo "  $(DIM)Not running$(RESET)"
	@echo ""
	@echo "$(CYAN)Host Services:$(RESET)"
	@for service in $(SERVICE_NAMES); do \
		if pgrep -f "$(SERVICES_DIR)/$$service" > /dev/null 2>&1; then \
			echo "  $(GREEN)●$(RESET) $$service $(DIM)(running)$(RESET)"; \
		else \
			echo "  $(DIM)○ $$service (stopped)$(RESET)"; \
		fi; \
	done

.PHONY: local-wait
local-wait: ## Wait for infrastructure to be ready
	@$(call print_info,"Waiting for infrastructure to be ready...")
	@scripts/wait-for-db.sh
	@$(call print_success,"Infrastructure is ready")
