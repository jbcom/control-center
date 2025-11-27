# Use mise for unified language runtime management
# https://mise.jdx.dev/
FROM jdxcode/mise:latest

# =============================================================================
# MISE CONFIGURATION & LANGUAGE RUNTIMES
# =============================================================================
# Set working directory first (mise looks for .mise.toml in working directory)
WORKDIR /workspace

# Copy mise configuration from repository root
COPY .mise.toml /workspace/.mise.toml

# Trust the mise config and install all language runtimes
# This handles: Python 3.13, Node.js 24, Rust stable, Go 1.23.4, just
RUN mise trust && mise install && mise reshim

# Enable mise in shell environment (mise shims are automatically in PATH)
# But we need to ensure the PATH is set correctly
ENV PATH="/root/.local/share/mise/shims:$PATH"

# =============================================================================
# SYSTEM DEPENDENCIES
# =============================================================================
# Single consolidated layer for all apt packages to minimize image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials (required for native modules: better-sqlite3, esbuild, etc.)
    build-essential \
    pkg-config \
    # Version control
    git-lfs \
    # GitHub CLI (Debian native package)
    gh \
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
    && rm -rf /var/lib/apt/lists/*

# Symlink fd-find to fd (Debian packages it as fdfind)
RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd

# =============================================================================
# GIT LFS CONFIGURATION
# =============================================================================
# CRITICAL: --skip-smudge prevents workspace crashes with large LFS repos
# AI tools (like Cursor) need file structure for code analysis, but not actual LFS content.
# This improves performance and reduces storage requirements in the dev environment.
# LFS files appear as pointers (text representation of metadata)
# Actual LFS operations (checkout, pull) handled by GitHub Actions or manual `git lfs pull`
RUN git lfs install --system --skip-smudge

# =============================================================================
# NODE.JS PACKAGE MANAGER (pnpm)
# =============================================================================
# pnpm version (line 70) MUST match package.json "packageManager" field exactly.
# PNPM_HOME path configuration (line 66) is independent and does not need to match package.json.
ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="$PNPM_HOME:$PATH"
# Enable corepack (comes with mise's Node.js) and install pnpm
RUN mise x -- corepack enable && \
    mise x -- corepack prepare pnpm@9.15.0 --activate && \
    mise x -- pnpm --version

# =============================================================================
# NODE.JS GLOBAL TOOLS
# =============================================================================
# Install Node.js tools globally that agents will need
RUN mise x -- pnpm install -g \
    # Ruler - Agent instruction management (https://ai.intellectronica.net/ruler)
    @intellectronica/ruler \
    # MCP Proxy - Bridge stdio MCP servers to HTTP/SSE for background agents
    mcp-proxy \
    # Cursor Background Agent MCP Server - Manage other Cursor background agents
    cursor-background-agent-mcp-server \
    # Verify installation
    && mise x -- ruler --version && \
    mise x -- mcp-proxy --version && \
    mise x -- cursor-background-agent-mcp-server --version

# =============================================================================
# RUST-BASED CLI TOOLS
# =============================================================================
# Rust toolchain is installed via mise (.mise.toml)
# Install additional Rust-based tools useful for background agents
RUN mise x -- cargo install --locked \
    # Modern ls replacement with icons
    exa \
    # Interactive process viewer
    bottom \
    # Fast code search
    ast-grep \
    # Modern cat replacement with syntax highlighting
    bat \
    # Git utilities
    git-delta \
    && rm -rf /root/.cargo/registry

# =============================================================================
# PYTHON TOOLING (using uv)
# =============================================================================
# Python is installed via mise (.mise.toml)
# Install uv for proper dependency management and global CLI tools
RUN mise x -- pip install --no-cache-dir uv && \
    mise x -- uv tool install ruff && \
    mise x -- uv tool install mypy && \
    mise x -- uv tool install pre-commit && \
    mise x -- uv tool install nox && \
    mise x -- uv tool install pycalver

# Verify uv and tools are available
RUN mise x -- uv --version && \
    mise x -- ruff --version && \
    mise x -- mypy --version && \
    mise x -- pre-commit --version

# Note: Package-specific dependencies (pytest, pyright, crewai, etc.) 
# should be defined in packages/*/pyproject.toml and installed with:
#   cd packages/<package> && uv sync
# Agent-specific tools (context-portal-mcp, crewai-tools) belong in 
# their respective package dependencies, not globally

# =============================================================================
# DEVELOPER TOOLS - process-compose
# =============================================================================
# Process-compose - Multi-process orchestration (required for CrewAI workflows)
# Using versioned binary for reproducibility and security
ENV PC_VERSION="v1.27.0"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/F1bonacc1/process-compose/releases/download/${PC_VERSION}/process-compose_${PC_VERSION}_linux_${ARCH}.tar.gz" \
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
# Pin specific version for reproducibility
ENV PLAYWRIGHT_VERSION="1.49.0"
RUN mise x -- pnpm dlx playwright@${PLAYWRIGHT_VERSION} install-deps chromium && \
    mise x -- pnpm dlx playwright@${PLAYWRIGHT_VERSION} install chromium

# =============================================================================
# GO-BASED DEVELOPER TOOLS
# =============================================================================
# Go toolchain is installed via mise (.mise.toml)
# Install useful Go-based tools
RUN mise x -- go install github.com/mikefarah/yq/v4@latest && \
    mise x -- go install github.com/jesseduffield/lazygit@latest && \
    mise x -- go install github.com/charmbracelet/glow@latest

# =============================================================================
# INFRASTRUCTURE & CLOUD TOOLS
# =============================================================================
# Tools for managing cloud infrastructure and secrets
# VERIFIED: 2025-11-27 from GitHub releases and official sources

# Terraform - version intentionally held at 1.13.1
# NOTE: Pinned to match enterprise infrastructure version
# DO NOT UPDATE until enterprise upgrades (check with infrastructure team)
# Latest available: 1.14.0 (as of 2025-11-27)
# VERIFIED: 2025-11-27 from https://github.com/hashicorp/terraform/releases
ENV TERRAFORM_VERSION="1.13.1"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" \
    -o /tmp/terraform.zip && \
    unzip -q /tmp/terraform.zip -d /usr/local/bin && \
    rm /tmp/terraform.zip && \
    chmod +x /usr/local/bin/terraform && \
    terraform version

# Terragrunt - latest stable
ENV TERRAGRUNT_VERSION="0.93.11"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/gruntwork-io/terragrunt/releases/download/v${TERRAGRUNT_VERSION}/terragrunt_linux_${ARCH}" \
    -o /usr/local/bin/terragrunt && \
    chmod +x /usr/local/bin/terragrunt && \
    terragrunt --version

# SOPS - secrets operations
ENV SOPS_VERSION="3.11.0"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.${ARCH}" \
    -o /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops && \
    sops --version

# AWS CLI v2 - latest stable
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip; \
    elif [ "$ARCH" = "aarch64" ]; then \
        curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscliv2.zip; \
    fi && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/aws /tmp/awscliv2.zip && \
    aws --version

# Google Cloud CLI - latest stable
ENV GCLOUD_VERSION="512.1.0"
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -sSL "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz" \
        -o /tmp/gcloud.tar.gz; \
    elif [ "$ARCH" = "aarch64" ]; then \
        curl -sSL "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-arm.tar.gz" \
        -o /tmp/gcloud.tar.gz; \
    fi && \
    tar -xzf /tmp/gcloud.tar.gz -C /usr/local && \
    rm /tmp/gcloud.tar.gz && \
    /usr/local/google-cloud-sdk/install.sh --quiet --usage-reporting false --path-update true && \
    ln -s /usr/local/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
    ln -s /usr/local/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
    gcloud version

# GAM - Google Workspace management
ENV GAM_VERSION="7.29.01"
RUN curl -sSL "https://github.com/GAM-team/GAM/releases/download/v${GAM_VERSION}/gam-${GAM_VERSION}-linux-x86_64.tar.xz" \
    -o /tmp/gam.tar.xz && \
    mkdir -p /usr/local/gam && \
    tar -xf /tmp/gam.tar.xz -C /usr/local/gam --strip-components=1 && \
    rm /tmp/gam.tar.xz && \
    ln -s /usr/local/gam/gam /usr/local/bin/gam && \
    gam version

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================
# Set up environment variables for optimal background agent operation
# Note: These are also defined in .mise.toml for consistency
ENV TERM=xterm-256color
ENV COLORTERM=truecolor
ENV EDITOR=vim
ENV PAGER=less

# Python optimizations
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Disable telemetry for various tools
ENV DO_NOT_TRACK=1
ENV DISABLE_TELEMETRY=1
ENV POWERSHELL_TELEMETRY_OPTOUT=1

# Working directory already set at top of Dockerfile for mise configuration
# Files will be copied by Cursor when container starts

# =============================================================================
# MCP BRIDGE SETUP
# =============================================================================
# Setup MCP bridge scripts after workspace is mounted
# Note: This runs AFTER Cursor copies workspace files
# Runtime bootstrap: ensure log directories exist and wire up MCP bridge wrappers when present
RUN cat <<'EOF' >/usr/local/bin/bootstrap-cursor-runtime.sh
#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
LOG_ROOT="${LOG_ROOT:-$WORKSPACE_ROOT/logs}"
CURSOR_ROOT="${CURSOR_ROOT:-$WORKSPACE_ROOT/.cursor}"
MEMORY_BANK_ROOT="${MEMORY_BANK_ROOT:-$WORKSPACE_ROOT/memory-bank}"

# Ensure .cursor directory exists for MCP bridge operations
mkdir -p "$CURSOR_ROOT"

# Check log directory status (agents create on first write)
if [ -d "$LOG_ROOT" ]; then
  echo "ℹ️  Logs directory present at $LOG_ROOT"
else
  echo "ℹ️  Logs directory missing; background agents will create it when they start writing"
fi

# Check global memory bank status (agents create during handoff if needed)
if [ -d "$MEMORY_BANK_ROOT" ]; then
  echo "✅ Global memory bank found at $MEMORY_BANK_ROOT"
else
  echo "ℹ️  Global memory bank not found at $MEMORY_BANK_ROOT; agents should create it during handoff if needed"
fi

# Link MCP bridge wrappers if available
SETUP_SCRIPT="$CURSOR_ROOT/scripts/mcp-bridge/setup.sh"
if [ -x "$SETUP_SCRIPT" ]; then
  echo "🔗 Linking MCP bridge wrappers via $SETUP_SCRIPT --global"
  if ! "$SETUP_SCRIPT" --global; then
    echo "⚠️  MCP bridge setup failed, but continuing (this may be expected if MCP bridge is not configured)"
  fi
else
  echo "ℹ️  Skipping MCP bridge linking; $SETUP_SCRIPT not present in workspace"
fi
EOF
RUN chmod +x /usr/local/bin/bootstrap-cursor-runtime.sh

# =============================================================================
# FINAL VERIFICATION
# =============================================================================
# Verify all critical tools are installed and working
RUN echo "=== VERIFICATION ===" && \
    echo "Mise:" && \
    mise --version && \
    echo "Languages:" && \
    mise x -- python --version && \
    mise x -- node --version && \
    mise x -- go version && \
    mise x -- rustc --version && \
    echo "Package Managers:" && \
    mise x -- pnpm --version && \
    mise x -- uv --version && \
    mise x -- cargo --version && \
    echo "Version Control:" && \
    git --version && \
    gh --version && \
    echo "Development Tools:" && \
    mise x -- just --version && \
    sqlite3 --version && \
    rg --version && \
    fd --version && \
    jq --version && \
    mise x -- ruff --version && \
    mise x -- mypy --version && \
    mise x -- pre-commit --version && \
    echo "Process & Browser:" && \
    process-compose version && \
    mise x -- ruler --version && \
    echo "Infrastructure & Cloud:" && \
    terraform version && \
    terragrunt --version && \
    sops --version && \
    aws --version && \
    gcloud version && \
    gam version && \
    echo "=== ALL TOOLS VERIFIED ==="
