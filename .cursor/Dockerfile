# Pre-built image with Python 3.13 + Node.js 24 + uv
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
    && rm -rf /var/lib/apt/lists/*

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
# DEVELOPER TOOLS
# =============================================================================
# Process-compose - Multi-process orchestration (required for CrewAI workflows)
# Using official installation script
ENV PC_VERSION="v1.27.0"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "" \
    -o /tmp/process-compose.tar.gz && \
    tar -xzf /tmp/process-compose.tar.gz -C /usr/local/bin process-compose && \
    chmod +x /usr/local/bin/process-compose && \
    rm /tmp/process-compose.tar.gz && \
    process-compose version

# =============================================================================
# PLAYWRIGHT BROWSER CACHE
# =============================================================================
# Pre-install Playwright dependencies and Chromium browser
# Playwright bundles its own Chromium (not using system package)
# This is required for CrewAI agents using @modelcontextprotocol/server-playwright
RUN pnpm dlx playwright@1.49.0 install-deps chromium && \
    pnpm dlx playwright@1.49.0 install chromium

WORKDIR /workspace
