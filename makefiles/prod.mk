# ================================================================
# PRODUCTION ENVIRONMENT
# ================================================================

.PHONY: prod
prod: prod-check ## Start production environment
	@$(call print_info,"Starting production environment...")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod up -d
	@$(MAKE) prod-wait
	@$(MAKE) prod-status
	@$(call print_success,"Production environment is running!")

.PHONY: prod-check
prod-check: ## Verify production configuration
	@test -f .env.prod || $(call print_error,".env.prod not found")
	@$(call print_info,"Checking production configuration...")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod config > /dev/null
	@$(call print_success,"Production configuration valid")

.PHONY: prod-build
prod-build: ## Build production Docker images
	@$(call print_info,"Building production images...")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod build --no-cache

.PHONY: prod-deploy
prod-deploy: prod-build ## Build and deploy to production
	@$(call print_header,"Production Deployment")
	@$(MAKE) prod-check
	@$(MAKE) prod-build
	@$(call print_info,"Deploying to production...")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod up -d --remove-orphans
	@$(MAKE) prod-wait
	@$(call print_success,"Production deployment complete!")

.PHONY: prod-stop
prod-stop: ## Stop production environment
	@$(call confirm,"This will stop production services")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod stop

.PHONY: prod-down
prod-down: ## Stop and remove production environment
	@$(call confirm,"This will remove production containers")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod down

.PHONY: prod-clean
prod-clean: ## Clean production environment (DANGEROUS)
	@$(call confirm,"WARNING: This will DELETE ALL PRODUCTION DATA")
	@$(call confirm,"Are you ABSOLUTELY SURE?")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod down -v

.PHONY: prod-logs
prod-logs: ## Show production logs
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod logs -f $(SERVICE)

.PHONY: prod-status
prod-status: ## Show production status
	@echo "$(CYAN)$(BOLD)PRODUCTION Environment:$(RESET)"
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null || echo "  $(DIM)Not running$(RESET)"

.PHONY: prod-wait
prod-wait: ## Wait for production services
	@$(call print_info,"Waiting for production services...")
	@sleep 10
	@scripts/health-check.sh prod
	@$(call print_success,"Production services are ready")

.PHONY: prod-backup
prod-backup: ## Backup production databases
	@$(call print_info,"Backing up production databases...")
	@mkdir -p backups/$(shell date +%Y%m%d)
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod exec -T postgres \
				pg_dump -U postgres -d $${service}_db > backups/$(shell date +%Y%m%d)/$$service.sql; \
		fi; \
	done
	@$(call print_success,"Backup complete: backups/$(shell date +%Y%m%d)/")

.PHONY: prod-rollback
prod-rollback: ## Rollback to previous version
	@$(call print_warning,"Rolling back to previous version...")
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod down
	@docker-compose -f $(COMPOSE_PROD) --project-name $(COMPOSE_PROJECT_NAME)-prod up -d
