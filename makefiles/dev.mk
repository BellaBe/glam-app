# ================================================================
# DEV ENVIRONMENT - Everything in Docker
# ================================================================

.PHONY: dev
dev: ## Start dev environment (all services in Docker)
	@$(call print_info,"Starting dev environment...")
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev up -d
	@$(MAKE) dev-wait
	@$(MAKE) dev-status
	@$(call print_success,"Dev environment is running!")

.PHONY: dev-build
dev-build: ## Build dev Docker images
	@$(call print_info,"Building dev images...")
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev build

.PHONY: dev-rebuild
dev-rebuild: ## Rebuild and restart dev environment
	@$(MAKE) dev-build
	@$(MAKE) dev

.PHONY: dev-stop
dev-stop: ## Stop dev environment
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev stop

.PHONY: dev-down
dev-down: ## Stop and remove dev environment
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev down

.PHONY: dev-clean
dev-clean: ## Clean dev environment (removes data)
	@$(call confirm,"This will delete all dev data")
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev down -v

.PHONY: dev-logs
dev-logs: ## Show dev logs (SERVICE=name for specific service)
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev logs -f $(SERVICE)

.PHONY: dev-restart
dev-restart: ## Restart a service in dev
	@$(call check_service,"dev-restart")
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev restart $(SERVICE)

.PHONY: dev-exec
dev-exec: ## Execute command in dev service
	@$(call check_service,"dev-exec")
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev exec $(SERVICE) $(CMD)

.PHONY: dev-status
dev-status: ## Show dev environment status
	@echo "$(CYAN)$(BOLD)DEV Environment:$(RESET)"
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  $(DIM)Not running$(RESET)"

.PHONY: dev-wait
dev-wait: ## Wait for dev services to be ready
	@$(call print_info,"Waiting for services to be ready...")
	@sleep 5
	@scripts/health-check.sh dev
	@$(call print_success,"All services are ready")

.PHONY: dev-scale
dev-scale: ## Scale a service in dev (SERVICE=name COUNT=3)
	@$(call check_service,"dev-scale")
	@test -n "$(COUNT)" || ($(call print_error,"COUNT not specified") && exit 1)
	@docker-compose -f $(COMPOSE_DEV) --project-name $(COMPOSE_PROJECT_NAME)-dev up -d --scale $(SERVICE)=$(COUNT)
