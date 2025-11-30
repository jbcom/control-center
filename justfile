# Justfile for jbcom control center monorepo
# https://github.com/casey/just

set shell := ["bash", "-cu"]
set dotenv-load

# Default recipe - show help
default:
    @just --list

# ============================================
# SETUP
# ============================================

# Install all packages with uv
install:
    uv sync

# Sync uv.lock
sync:
    uv sync

# ============================================
# RULER (AI Agent Instructions)
# ============================================

# Apply ruler to generate all agent config files (nested mode)
ruler:
    ruler apply --nested

# Apply ruler with verbose output
ruler-verbose:
    ruler apply --nested --verbose

# Apply ruler dry-run (show what would change)
ruler-dry:
    ruler apply --nested --dry-run

# Clean ruler backup files (they should never be in SCM)
ruler-clean:
    find . -name "*.bak" -type f -delete
    @echo "Cleaned up .bak files"

# ============================================
# TESTING
# ============================================

# Run tests for all packages
test:
    #!/usr/bin/env bash
    set -e
    for pkg in extended-data-types lifecyclelogging directed-inputs-class python-terraform-bridge vendor-connectors; do
        echo "=== Testing $pkg ==="
        cd packages/$pkg && uv run pytest tests && cd ../..
    done

# Run tests for a specific package
test-pkg package:
    cd packages/{{package}} && uv run pytest tests

# Run tests with tox (all Python versions)
tox:
    uvx --with tox-uv tox

# Run tox for a specific package
tox-pkg package:
    uvx --with tox-uv tox -e {{package}}

# Run tests with coverage
test-cov:
    uvx --with tox-uv tox -e extended-data-types,lifecyclelogging,directed-inputs-class,python-terraform-bridge,vendor-connectors
    uvx --with tox-uv tox -e coverage-combine,coverage-report

# ============================================
# CODE QUALITY
# ============================================

# Run ruff linter
lint:
    uvx ruff check packages/

# Format code with ruff
format:
    uvx ruff format packages/
    uvx ruff check --fix packages/

# Run mypy type checker
typecheck:
    uv run mypy packages/extended-data-types/src --ignore-missing-imports
    uv run mypy packages/lifecyclelogging/src --ignore-missing-imports

# Run all quality checks (lint + typecheck)
check: lint typecheck

# Fix all auto-fixable issues
fix:
    uvx ruff check --fix packages/
    uvx ruff format packages/

# ============================================
# BUILDING
# ============================================

# Build all packages
build:
    #!/usr/bin/env bash
    set -e
    mkdir -p dist
    for pkg in extended-data-types lifecyclelogging directed-inputs-class python-terraform-bridge vendor-connectors; do
        echo "=== Building $pkg ==="
        cd packages/$pkg && uv build --out-dir ../../dist && cd ../..
    done

# Build a specific package
build-pkg package:
    cd packages/{{package}} && uv build

# ============================================
# DOCUMENTATION
# ============================================

# Build docs for extended-data-types (the main documented package)
docs:
    cd packages/extended-data-types && uv run sphinx-build -n -b html docs docs/_build/html

# Build docs with live reload
docs-watch:
    cd packages/extended-data-types && uv run sphinx-autobuild docs docs/_build/html

# ============================================
# CI SIMULATION
# ============================================

# Simulate CI build (build all packages, run all tests)
ci: build
    #!/usr/bin/env bash
    set -e
    export UV_FIND_LINKS=./dist
    for pkg in extended-data-types lifecyclelogging directed-inputs-class python-terraform-bridge vendor-connectors; do
        echo "=== Testing $pkg (CI mode) ==="
        WHEEL_NAME=$(echo "$pkg" | tr '-' '_')
        uvx --with tox-uv tox run --installpkg dist/${WHEEL_NAME}-*.whl -e $pkg
    done

# ============================================
# MAINTENANCE
# ============================================

# Clean build artifacts
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".coverage*" -delete 2>/dev/null || true
    find . -name "*.bak" -type f -delete 2>/dev/null || true
    @echo "Cleaned!"

# Update all dependencies
update:
    uv lock --upgrade

# Show outdated dependencies
outdated:
    uv pip list --outdated

# ============================================
# RELEASE (local prep only - CI handles actual release)
# ============================================

# Check what would be released (dry run)
release-check package:
    cd packages/{{package}} && semantic-release --noop version

# Show release status for all packages
release-status:
    #!/usr/bin/env bash
    for pkg in extended-data-types lifecyclelogging directed-inputs-class python-terraform-bridge vendor-connectors; do
        echo "=== $pkg ==="
        cd packages/$pkg
        VERSION=$(grep '^version = ' pyproject.toml | head -1 | sed 's/version = "\([^"]*\)"/\1/')
        echo "Current version: $VERSION"
        semantic-release --noop version 2>&1 | head -5 || true
        cd ../..
        echo ""
    done
