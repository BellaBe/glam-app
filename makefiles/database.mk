# ================================================================
# DATABASE MANAGEMENT
# ================================================================

.PHONY: db-url
db-url: ## Get database URL for a service
	@$(call check_service,"db-url")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)); \
	echo "$(CYAN)DATABASE_URL for $(SERVICE):$(RESET)"; \
	echo "$$DATABASE_URL"


.PHONY: db-push
db-push: ## Push Prisma schema to database
	@$(call check_service,"db-push")
	@$(call print_info,"Pushing schema for $(SERVICE)...")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)) && \
	cd $(SERVICES_DIR)/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma db push --accept-data-loss

.PHONY: db-migrate
db-migrate: ## Create and apply migration
	@$(call check_service,"db-migrate")
	@test -n "$(NAME)" || ($(call print_error,"NAME not specified. Usage: make db-migrate SERVICE=x NAME='add_field'") && exit 1)
	@$(call print_info,"Creating migration '$(NAME)' for $(SERVICE)...")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)) && \
	cd $(SERVICES_DIR)/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma migrate dev --name $(NAME)

.PHONY: db-reset
db-reset: ## Reset database (removes all data)
	@$(call check_service,"db-reset")
	@$(call confirm,"This will delete all data in $(SERVICE) database")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)) && \
	cd $(SERVICES_DIR)/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma migrate reset --force --skip-seed

.PHONY: db-studio
db-studio: ## Open Prisma Studio
	@$(call check_service,"db-studio")
	@$(call print_info,"Opening Prisma Studio for $(SERVICE)...")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)) && \
	cd $(SERVICES_DIR)/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run prisma studio

.PHONY: db-seed
db-seed: ## Seed database with sample data
	@$(call check_service,"db-seed")
	@$(call print_info,"Seeding $(SERVICE) database...")
	@DATABASE_URL=$$(scripts/get-db-url.sh $(SERVICE) $(ENV)) && \
	cd $(SERVICES_DIR)/$(SERVICE) && \
		DATABASE_URL="$$DATABASE_URL" \
		poetry run python scripts/seed.py

.PHONY: db-status
db-status: ## Check database status
	@$(call print_header,"Database Status")
	@for service in $(SERVICE_NAMES); do \
		if [ -f "$(SERVICES_DIR)/$$service/prisma/schema.prisma" ]; then \
			echo "$(CYAN)$$service:$(RESET)"; \
			DATABASE_URL=$$(scripts/get-db-url.sh $$service $(ENV) 2>/dev/null) && \
			echo "  URL: $$DATABASE_URL" || echo "  $(RED)Not configured$(RESET)"; \
		fi; \
	done
