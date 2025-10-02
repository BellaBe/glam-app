# ================================================================
# GLAM APP MONOREPO - MAIN ORCHESTRATOR
# ================================================================

# Default environment
ENV ?= local

# Load environment files
-include .env
-include .env.$(ENV)

# Load modular makefiles
include makefiles/common.mk
include makefiles/local.mk
include makefiles/dev.mk
include makefiles/prod.mk
include makefiles/database.mk
include makefiles/services.mk
-include makefiles/precommit.mk

# Default target
.DEFAULT_GOAL := help

# ================================================================
# MAIN TARGETS
# ================================================================

.PHONY: help
help: ## Show this help message
	@$(call print_header,"Glam App Monorepo")
	@echo "$(YELLOW)Usage:$(RESET) make [target] [ENV=local|dev|prod] [SERVICE=service-name]"
	@echo ""
	@echo "$(CYAN)$(BOLD)Quick Start:$(RESET)"
	@echo "  make local              $(DIM)# Start local development (infra in Docker, services on host)$(RESET)"
	@echo "  make dev                $(DIM)# Start dev environment (everything in Docker)$(RESET)"
	@echo "  make prod               $(DIM)# Start production environment$(RESET)"
	@echo ""
	@echo "$(CYAN)$(BOLD)Available Targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' | \
		sort
	@echo ""
	@echo "$(CYAN)$(BOLD)Available Services:$(RESET)"
	@for service in $(SERVICE_NAMES); do \
		printf "  $(GREEN)•$(RESET) %-30s" "$$service"; \
		if [ -f "services/$$service/prisma/schema.prisma" ]; then \
			echo "$(DIM)[Prisma]$(RESET)"; \
		else \
			echo ""; \
		fi; \
	done

.PHONY: init
init: ## Initialize the monorepo for first use
	@$(call print_header,"Initializing Monorepo")
	@$(MAKE) check-deps
	@$(MAKE) setup-env
	@$(call print_success,"Initialization complete! Run 'make local' to start developing")

.PHONY: status
status: ## Show status of all environments
	@$(call print_header,"System Status")
	@$(MAKE) -s local-status 2>/dev/null || true
	@$(MAKE) -s dev-status 2>/dev/null || true
	@$(MAKE) -s prod-status 2>/dev/null || true

.PHONY: clean-all
clean-all: ## Clean everything (containers, volumes, caches)
	@$(call confirm,"This will remove ALL Docker resources and caches")
	@$(MAKE) local-clean
	@$(MAKE) dev-clean
	@$(MAKE) prod-clean
	@$(MAKE) clean-cache
	@$(call print_success,"Complete cleanup done")
