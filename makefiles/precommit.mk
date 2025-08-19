# makefiles/precommit.mk
# ========================================
# Pre-commit and Cache Management
# ========================================

.PHONY: clean-cache
clean-cache:  ## Clear all Python and pre-commit caches
	@echo "🧹 Clearing all caches..."
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf .coverage.* 2>/dev/null || true
	@echo "✅ All caches cleared"

.PHONY: clean-precommit
clean-precommit:  ## Clean and reinstall pre-commit
	@echo "🧹 Cleaning pre-commit..."
	@pre-commit clean
	@pre-commit uninstall
	@rm -rf ~/.cache/pre-commit/ 2>/dev/null || true
	@echo "✅ Pre-commit cleaned"

.PHONY: install-precommit
install-precommit:  ## Install pre-commit hooks
	@echo "📦 Installing pre-commit..."
	@pre-commit install
	@pre-commit install-hooks
	@echo "✅ Pre-commit installed"

.PHONY: update-precommit
update-precommit:  ## Update pre-commit hooks to latest versions
	@echo "🔄 Updating pre-commit hooks..."
	@pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

.PHONY: fresh-precommit
fresh-precommit: clean-cache clean-precommit install-precommit  ## Complete fresh pre-commit setup
	@echo "🎉 Fresh pre-commit setup complete!"

.PHONY: run-precommit
run-precommit:  ## Run pre-commit on all files
	@echo "🏃 Running pre-commit on all files..."
	@pre-commit run --all-files

.PHONY: run-precommit-staged
run-precommit-staged:  ## Run pre-commit on staged files only
	@echo "🏃 Running pre-commit on staged files..."
	@pre-commit run

.PHONY: fix-precommit
fix-precommit:  ## Run pre-commit with auto-fixing
	@echo "🔧 Running pre-commit with auto-fix..."
	@pre-commit run --all-files || pre-commit run --all-files

.PHONY: mypy-services
mypy-services:  ## Run mypy on all services
	@echo "🔍 Running mypy on all services..."
	@python .pre-commit-scripts/run_mypy.py

.PHONY: mypy-clean
mypy-clean: clean-cache mypy-services  ## Clear mypy cache and run checks
	@echo "✅ Mypy check complete with fresh cache"

.PHONY: fresh-check
fresh-check: fresh-precommit run-precommit  ## Fresh setup and run all checks
	@echo "✅ Fresh check complete!"

.PHONY: quick-check
quick-check:  ## Quick pre-commit check without cleaning
	@pre-commit run --all-files
