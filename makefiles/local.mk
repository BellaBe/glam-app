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

.PHONY: local-wait
local-wait: ## Wait for infrastructure to be ready
	@$(call print_info,"Waiting for infrastructure to be ready...")
	@scripts/wait-for-db.sh
	@$(call print_success,"Infrastructure is ready")

# ================================================================
# SINGLE SERVICE OPERATIONS
# ================================================================

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

# ================================================================
# BATCH SERVICE OPERATIONS
# ================================================================

.PHONY: setup-all
setup-all: ## Setup all services (install deps + generate Prisma)
	@$(call print_header,"Setting Up All Services")
	@for service in $(SERVICE_NAMES); do \
		echo "$(CYAN)Setting up $$service...$(RESET)"; \
		(cd $(SERVICES_DIR)/$$service && \
		poetry install --sync && \
		if [ -f prisma/schema.prisma ]; then \
			echo "  Generating Prisma client..."; \
			poetry run prisma generate; \
		fi) && \
		echo "$(GREEN)✅ $$service ready$(RESET)" || \
		echo "$(RED)❌ Failed to setup $$service$(RESET)"; \
		echo ""; \
	done
	@$(call print_success,"All services setup complete!")

.PHONY: clean-venv
clean-venv: ## Clean all virtual environments
	@echo "🧹 Cleaning all virtual environments..."
	@for dir in services/*; do \
		if [ -d "$$dir/.venv" ]; then \
			echo "Removing $$dir/.venv"; \
			rm -rf "$$dir/.venv"; \
		fi \
	done

.PHONY: update-locks
update-locks: ## Update all poetry lock files
	@echo "🔄 Updating all lock files..."
	@for dir in services/*; do \
		if [ -f "$$dir/pyproject.toml" ]; then \
			echo "Updating lock for $$dir..."; \
			(cd "$$dir" && poetry lock --no-update); \
		fi \
	done

.PHONY: reinstall-all
reinstall-all: clean-venv update-locks setup-all ## Clean reinstall all services
	@$(call print_success,"All services reinstalled with fresh dependencies!")

# ================================================================
# DATABASE OPERATIONS
# ================================================================

.PHONY: db-push-all
db-push-all: ## Push all Prisma schemas to databases
	@$(call print_header,"Pushing All Database Schemas")
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "$(CYAN)Pushing schema for $$service...$(RESET)"; \
			SERVICE_NAME=$$(echo $$service | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); \
			DB_USER=$$(grep "$${SERVICE_NAME}_DB_USER" .env | cut -d '=' -f2); \
			DB_PASSWORD=$$(grep "$${SERVICE_NAME}_DB_PASSWORD" .env | cut -d '=' -f2); \
			DB_NAME=$$(grep "$${SERVICE_NAME}_DB_NAME" .env | cut -d '=' -f2); \
			DB_PORT=$$(grep "$${SERVICE_NAME}_DB_PORT_EXTERNAL" .env | cut -d '=' -f2); \
			(cd $(SERVICES_DIR)/$$service && \
			DATABASE_URL="postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}" \
			poetry run prisma db push --accept-data-loss) || echo "$(RED)Failed: $$service$(RESET)"; \
		else \
			echo "$(DIM)Skipping $$service (no database)$(RESET)"; \
		fi; \
	done
	@$(call print_success,"All schemas pushed!")

.PHONY: db-reset-all
db-reset-all: ## Reset all databases (DESTRUCTIVE)
	@echo "$(RED)⚠️  WARNING: This will DELETE ALL DATA in all databases!$(RESET)"
	@read -p "Are you sure? [y/N]: " confirm && ([ "$$confirm" = "y" ] || [ "$$confirm" = "yes" ]) || exit 1
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "$(YELLOW)Resetting database for $$service...$(RESET)"; \
			SERVICE_NAME=$$(echo $$service | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); \
			DB_USER=$$(grep "$${SERVICE_NAME}_DB_USER" .env | cut -d '=' -f2); \
			DB_PASSWORD=$$(grep "$${SERVICE_NAME}_DB_PASSWORD" .env | cut -d '=' -f2); \
			DB_NAME=$$(grep "$${SERVICE_NAME}_DB_NAME" .env | cut -d '=' -f2); \
			DB_PORT=$$(grep "$${SERVICE_NAME}_DB_PORT_EXTERNAL" .env | cut -d '=' -f2); \
			(cd $(SERVICES_DIR)/$$service && \
			DATABASE_URL="postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}" \
			poetry run prisma migrate reset --force --skip-seed 2>/dev/null || \
			DATABASE_URL="postgresql://$${DB_USER}:$${DB_PASSWORD}@localhost:$${DB_PORT}/$${DB_NAME}" \
			poetry run prisma db push --force-reset --accept-data-loss); \
		fi; \
	done
	@echo "$(GREEN)✅ All databases reset!$(RESET)"

.PHONY: services-status
services-status: ## Show status of all services with database info
	@$(call print_header,"Services Status")
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "$(GREEN)✓$(RESET) $$service $(DIM)(has database)$(RESET)"; \
			if [ -d "$(SERVICES_DIR)/$$service/.venv" ]; then \
				echo "  $(GREEN)●$(RESET) Poetry environment installed"; \
			else \
				echo "  $(RED)○$(RESET) Poetry environment missing"; \
			fi; \
		else \
			echo "$(YELLOW)○$(RESET) $$service $(DIM)(no database)$(RESET)"; \
			if [ -d "$(SERVICES_DIR)/$$service/.venv" ]; then \
				echo "  $(GREEN)●$(RESET) Poetry environment installed"; \
			else \
				echo "  $(RED)○$(RESET) Poetry environment missing"; \
			fi; \
		fi; \
	done

# ================================================================
# COMPLETE RESET OPERATIONS
# ================================================================

.PHONY: reset-all
reset-all: ## Complete reset: infrastructure + all services + databases
	@$(call print_header,"COMPLETE SYSTEM RESET")
	@echo "$(RED)This will:$(RESET)"
	@echo "  1. Stop and remove all infrastructure"
	@echo "  2. Delete all database data"
	@echo "  3. Remove all virtual environments"
	@echo "  4. Reinstall everything from scratch"
	@echo ""
	@read -p "Type 'RESET' to continue: " confirm && [ "$$confirm" = "RESET" ] || exit 1
	@echo ""
	@echo "$(YELLOW)Step 1/5: Stopping infrastructure...$(RESET)"
	@docker-compose -f $(COMPOSE_INFRA) --project-name $(COMPOSE_PROJECT_NAME)-local down -v
	@echo "$(YELLOW)Step 2/5: Cleaning virtual environments...$(RESET)"
	@$(MAKE) clean-venv
	@echo "$(YELLOW)Step 3/5: Starting fresh infrastructure...$(RESET)"
	@$(MAKE) local-infra
	@echo "$(YELLOW)Step 4/5: Installing all services...$(RESET)"
	@$(MAKE) setup-all
	@echo "$(YELLOW)Step 5/5: Pushing database schemas...$(RESET)"
	@$(MAKE) db-push-all
	@$(call print_success,"COMPLETE RESET FINISHED! System ready for development.")

.PHONY: quick-reset
quick-reset: ## Quick reset: just databases and Prisma clients
	@echo "$(CYAN)Starting quick reset of databases and Prisma clients...$(RESET)"
	@$(MAKE) db-reset-all
	@$(MAKE) db-push-all
	@echo "$(CYAN)Regenerating Prisma clients...$(RESET)"
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "  Generating Prisma client for $$service..."; \
			(cd $(SERVICES_DIR)/$$service && poetry run prisma generate); \
		fi; \
	done
	@echo "$(GREEN)✅ Quick reset complete!$(RESET)"

# ================================================================
# HELPER COMMANDS
# ================================================================

.PHONY: fix-imports
fix-imports: ## Fix Python imports in all services
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/pyproject.toml" ]; then \
			echo "Fixing imports in $$service..."; \
			cd $(SERVICES_DIR)/$$service && \
			poetry run isort . && \
			poetry run black .; \
		fi; \
	done

.PHONY: test-connections
test-connections: ## Test database connections for all services
	@$(call print_header,"Testing Database Connections")
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			SERVICE_NAME=$$(echo $$service | sed 's/-service//' | sed 's/-/_/g' | tr a-z A-Z); \
			DB_PORT=$$(grep "$${SERVICE_NAME}_DB_PORT_EXTERNAL" .env | cut -d '=' -f2); \
			if docker exec -t $$(echo $$service | sed 's/-service/-db-local/') pg_isready 2>/dev/null; then \
				echo "$(GREEN)✓$(RESET) $$service database is ready (port $$DB_PORT)"; \
			else \
				echo "$(RED)✗$(RESET) $$service database is not responding"; \
			fi; \
		fi; \
	done
