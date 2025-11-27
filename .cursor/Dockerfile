# Pre-built image with Python 3.13 + Node.js 24
# https://github.com/nikolaik/docker-python-nodejs
FROM nikolaik/python-nodejs:python3.13-nodejs24

# =============================================================================
# SYSTEM DEPENDENCIES
# =============================================================================
# Single consolidated layer for all apt packages to minimize image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials (required for native Node modules: better-sqlite3, esbuild, etc.)
    build-essential \
    pkg-config \
    # Version control
    git-lfs \
    # GitHub CLI (Debian native package)
    gh \
    # Task automation (Debian native package)
    just \
    # Database tools (for ConPort SQLite database)
    sqlite3 \
    # Modern shell utilities (faster alternatives to find/grep)
    ripgrep \
    fd-find \
    # JSON/YAML processing
    jq \
    # Text editors for quick edits
    vim \
    nano \
    # Network tools
    curl \
    wget \
    ca-certificates \
    # Process management
    procps \
    htop \
    # Compression tools
    unzip \
    zip \
    # Playwright/Chromium browser dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Symlink fd-find to fd (Debian packages it as fdfind)
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

# =============================================================================
# GIT LFS CONFIGURATION
# =============================================================================
# CRITICAL: --skip-smudge prevents workspace crashes with large LFS repos
# LFS files appear as pointers (fine for Cursor/AI analysis)
# Actual LFS operations (checkout, pull) handled by GitHub Actions
RUN git lfs install --system --skip-smudge

# =============================================================================
# NODE.JS PACKAGE MANAGER (pnpm)
# =============================================================================
# MUST match package.json "packageManager" field exactly
ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && \
    corepack prepare pnpm@9.15.0 --activate && \
    pnpm --version

# =============================================================================
# PYTHON TOOLING (using uv)
# =============================================================================
# Note: uv is already installed in the base image (nikolaik/python-nodejs)
# Verify it's available
RUN uv --version

# Python optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# =============================================================================
# DEVELOPER TOOLS - BINARIES
# =============================================================================
# Process-compose - Multi-process orchestration tool (standalone binary)
# This is NOT a Python/Node package - it's a compiled Go binary
ENV PC_VERSION="v1.27.0"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/F1bonacc1/process-compose/releases/download/${PC_VERSION}/process-compose_${PC_VERSION}_linux_${ARCH}.tar.gz" \
    -o /tmp/process-compose.tar.gz && \
    tar -xzf /tmp/process-compose.tar.gz -C /usr/local/bin process-compose && \
    chmod +x /usr/local/bin/process-compose && \
    rm /tmp/process-compose.tar.gz && \
    process-compose version

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================
# Set up environment variables for optimal background agent operation
ENV TERM=xterm-256color
ENV COLORTERM=truecolor
ENV EDITOR=vim
ENV PAGER=less

# Disable telemetry for various tools
ENV DO_NOT_TRACK=1
ENV DISABLE_TELEMETRY=1
ENV POWERSHELL_TELEMETRY_OPTOUT=1

WORKDIR /workspace

# =============================================================================
# WORKSPACE PYTHON DEV TOOLS
# =============================================================================
# Note: Python dev tools (ruff, mypy, pre-commit, nox, pytest, pyright, pycalver)
# are defined in the root pyproject.toml [project.optional-dependencies.dev]
# 
# When the workspace is mounted, run:
#   uv sync --extra dev
# 
# This installs all dev tools from the UV workspace configuration.
# The tools will be available in the virtual environment at .venv/

# =============================================================================
# FINAL VERIFICATION
# =============================================================================
# Verify all critical tools are installed and working
RUN echo "=== VERIFICATION ===" && \
    echo "Languages:" && \
    python --version && \
    node --version && \
    echo "Package Managers:" && \
    pnpm --version && \
    uv --version && \
    echo "Version Control:" && \
    git --version && \
    gh --version && \
    echo "Development Tools:" && \
    just --version && \
    sqlite3 --version && \
    rg --version && \
    fd --version && \
    jq --version && \
    process-compose version && \
    echo "=== ALL TOOLS VERIFIED ===" && \
    echo "" && \
    echo "🎯 Workspace ready! Agents can install packages with:" && \
    echo "  - Python: uv sync --extra dev" && \
    echo "  - Node.js: pnpm install" && \
    echo "  - Playwright: pnpm dlx playwright@latest install chromium" && \
    echo "  - Or use direnv with .envrc for auto-setup"
