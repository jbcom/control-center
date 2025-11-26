# Makefile for jbcom control center monorepo

.DEFAULT_GOAL := help

# Packages in dependency order
PACKAGES := extended-data-types lifecyclelogging directed-inputs-class vendor-connectors

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install all packages with uv"
	@echo "  sync         Sync uv.lock"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run tests for all packages"
	@echo "  test-PKG     Run tests for specific package (e.g., test-extended-data-types)"
	@echo "  tox          Run tox for all Python versions"
	@echo ""
	@echo "Quality:"
	@echo "  lint         Run ruff linter"
	@echo "  format       Format code with ruff"
	@echo "  typecheck    Run mypy"
	@echo "  check        Run lint + typecheck"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Remove build artifacts"
	@echo "  bump         Bump version with pycalver (dry run)"

# Setup
.PHONY: install
install:
	uv sync

.PHONY: sync
sync:
	uv sync

# Testing - all packages
.PHONY: test
test:
	@for pkg in $(PACKAGES); do \
		echo "=== Testing $$pkg ==="; \
		cd packages/$$pkg && uv run pytest tests && cd ../..; \
	done

# Testing - individual packages
.PHONY: test-extended-data-types
test-extended-data-types:
	cd packages/extended-data-types && uv run pytest tests

.PHONY: test-lifecyclelogging
test-lifecyclelogging:
	cd packages/lifecyclelogging && uv run pytest tests

.PHONY: test-directed-inputs-class
test-directed-inputs-class:
	cd packages/directed-inputs-class && uv run pytest tests

.PHONY: test-vendor-connectors
test-vendor-connectors:
	cd packages/vendor-connectors && uv run pytest tests

# Tox
.PHONY: tox
tox:
	uv run tox

# Quality
.PHONY: lint
lint:
	uv run ruff check packages/

.PHONY: format
format:
	uv run ruff format packages/
	uv run ruff check --fix packages/

.PHONY: typecheck
typecheck:
	uv run mypy packages/extended-data-types/src
	uv run mypy packages/lifecyclelogging/src

.PHONY: check
check: lint typecheck

# Maintenance
.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

.PHONY: bump
bump:
	pycalver bump --dry
