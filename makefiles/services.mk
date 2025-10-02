# ================================================================
# SERVICE MANAGEMENT
# ================================================================

.PHONY: service-list
service-list: ## List all services
	@$(call print_header,"Available Services")
	@for service in $(SERVICE_NAMES); do \
		echo "$(GREEN)$$service$(RESET)"; \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "  Type: Python/FastAPI with Prisma"; \
		else \
			echo "  Type: Python/FastAPI"; \
		fi; \
		if [ -f "$(SERVICES_DIR)/$$service/.env" ]; then \
			PORT=$$(grep "PORT=" "$(SERVICES_DIR)/$$service/.env" | cut -d'=' -f2); \
			echo "  Port: $$PORT"; \
		fi; \
	done

.PHONY: service-create
service-create: ## Create a new service from template
	@test -n "$(NAME)" || ($(call print_error,"NAME not specified. Usage: make service-create NAME=new-service") && exit 1)
	@$(call print_info,"Creating service $(NAME)...")
	@cp -r $(SERVICES_DIR)/template $(SERVICES_DIR)/$(NAME)
	@sed -i 's/template/$(NAME)/g' $(SERVICES_DIR)/$(NAME)/pyproject.toml
	@$(call print_success,"Service $(NAME) created")

.PHONY: service-test
service-test: ## Run tests for a service
	@$(call check_service,"service-test")
	@$(call print_info,"Running tests for $(SERVICE)...")
	@cd $(SERVICES_DIR)/$(SERVICE) && poetry run pytest

.PHONY: service-lint
service-lint: ## Lint a service
	@$(call check_service,"service-lint")
	@$(call print_info,"Linting $(SERVICE)...")
	@cd $(SERVICES_DIR)/$(SERVICE) && \
		poetry run black . && \
		poetry run isort . && \
		poetry run mypy .

.PHONY: service-deps-update
service-deps-update: ## Update service dependencies
	@$(call check_service,"service-deps-update")
	@$(call print_info,"Updating dependencies for $(SERVICE)...")
	@cd $(SERVICES_DIR)/$(SERVICE) && poetry update

.PHONY: services-install-all
services-install-all: ## Install all service dependencies
	@$(call print_header,"Installing All Services")
	@for service in $(SERVICE_NAMES); do \
		$(call print_info,"Installing $$service..."); \
		cd $(SERVICES_DIR)/$$service && poetry install --sync; \
	done
	@$(call print_success,"All services installed")

.PHONY: services-clean
services-clean: ## Clean all service caches and virtual envs
	@$(call print_info,"Cleaning service environments...")
	@for service in $(SERVICE_NAMES); do \
		rm -rf $(SERVICES_DIR)/$$service/.venv; \
		rm -rf $(SERVICES_DIR)/$$service/__pycache__; \
		rm -rf $(SERVICES_DIR)/$$service/.pytest_cache; \
		rm -rf $(SERVICES_DIR)/$$service/.mypy_cache; \
	done
	@$(call print_success,"Services cleaned")
