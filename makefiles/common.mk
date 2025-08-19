# ================================================================
# COMMON CONFIGURATION
# ================================================================

# Shell settings
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables --no-builtin-rules

# Paths
ROOT_DIR := $(shell pwd)
SERVICES_DIR := services

# Auto-discovery
SERVICE_DIRS := $(shell find $(SERVICES_DIR) -maxdepth 1 -type d \
	\( -name "*-service" -o -name "*-ai-*" -o -name "*-connector" -o -name "*-cache" \) | sort)
SERVICE_NAMES := $(notdir $(SERVICE_DIRS))

# Docker compose files
COMPOSE_INFRA := docker-compose.local.yml
COMPOSE_DEV := docker-compose.dev.yml
COMPOSE_PROD := docker-compose.prod.yml

# Project settings
COMPOSE_PROJECT_NAME ?= glam-app

# Colors
RESET := \033[0m
BOLD := \033[1m
DIM := \033[2m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
CYAN := \033[36m

# ================================================================
# FIXED HELPER FUNCTIONS - No @ symbols inside definitions!
# ================================================================

# Print header
define print_header
echo "" && \
echo "$(BLUE)$(BOLD)════════════════════════════════════════════════$(RESET)" && \
echo "$(BLUE)$(BOLD)  $(1)$(RESET)" && \
echo "$(BLUE)$(BOLD)════════════════════════════════════════════════$(RESET)" && \
echo ""
endef

# Print success message
define print_success
echo "$(GREEN)✅ $(1)$(RESET)"
endef

# Print error and exit - simplified to avoid issues
define print_error
echo "$(RED)❌ $(1)$(RESET)" >&2; exit 1
endef

# Print warning
define print_warning
echo "$(YELLOW)⚠️  $(1)$(RESET)"
endef

# Print info
define print_info
echo "$(CYAN)ℹ️  $(1)$(RESET)"
endef

# Confirm action
define confirm
echo "$(YELLOW)⚠️  $(1)$(RESET)" && \
read -p "Continue? [y/N]: " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
endef

# Check service - simplified to avoid nested function calls
define check_service
test -n "$(SERVICE)" || { echo "$(RED)❌ SERVICE not specified. Usage: make $(1) SERVICE=webhook-service$(RESET)" >&2; exit 1; } && \
test -d "$(SERVICES_DIR)/$(SERVICE)" || { echo "$(RED)❌ Service '$(SERVICE)' not found$(RESET)" >&2; exit 1; }
endef

# ================================================================
# DEPENDENCY CHECKS
# ================================================================

.PHONY: check-deps
check-deps: ## Check required dependencies
	@$(call print_info,Checking dependencies...)
	@command -v docker >/dev/null 2>&1 || { $(call print_error,Docker not installed); }
	@command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || \
		{ $(call print_error,Docker Compose not installed); }
	@command -v poetry >/dev/null 2>&1 || $(call print_warning,Poetry not installed (required for Python services))
	@$(call print_success,All required dependencies found)

# Environment setup
.PHONY: setup-env
setup-env: ## Setup environment files
	@test -f .env || { cp .env.example .env && $(call print_info,Created .env from .env.example); }
	@test -f .env.local || { cp .env.example .env.local && $(call print_info,Created .env.local); }
	@test -f .env.dev || { cp .env.example .env.dev && $(call print_info,Created .env.dev); }
	@test -f .env.prod || { cp .env.example .env.prod && $(call print_info,Created .env.prod); }
