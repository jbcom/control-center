# Pre-built image with Python 3.13 + Node.js 24 + uv
# https://github.com/nikolaik/docker-python-nodejs
FROM nikolaik/python-nodejs:python3.13-nodejs24

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
# pnpm version (line 63) MUST match package.json "packageManager" field exactly.
# PNPM_HOME path configuration (line 59) is independent and does not need to match package.json.
ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && \
    corepack prepare pnpm@9.15.0 --activate && \
    pnpm --version

# =============================================================================
# NODE.JS GLOBAL TOOLS
# =============================================================================
# Install Node.js tools globally that agents will need
RUN pnpm install -g \
    # Ruler - Agent instruction management (https://ai.intellectronica.net/ruler)
    @intellectronica/ruler \
    # MCP Proxy - Bridge stdio MCP servers to HTTP/SSE for background agents
    mcp-proxy \
    # Verify installation
    && ruler --version && \
    mcp-proxy --version

# =============================================================================
# RUST TOOLING (for modern CLI tools)
# =============================================================================
# Many modern development tools are written in Rust
# Installing via rustup for latest stable versions
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:$PATH"

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal && \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME && \
    rustc --version && cargo --version

# Install additional Rust-based tools useful for background agents
RUN cargo install --locked \
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
    && rm -rf $CARGO_HOME/registry

# =============================================================================
# PYTHON TOOLING (using uv from base image)
# =============================================================================
# Base image includes uv - use it for proper dependency management
# Install global CLI tools with uv tool install
RUN uv tool install ruff && \
    uv tool install mypy && \
    uv tool install pre-commit && \
    uv tool install nox && \
    uv tool install pycalver

# Verify uv and tools are available
RUN uv --version && \
    ruff --version && \
    mypy --version && \
    pre-commit --version

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
RUN pnpm dlx playwright@${PLAYWRIGHT_VERSION} install-deps chromium && \
    pnpm dlx playwright@${PLAYWRIGHT_VERSION} install chromium

# =============================================================================
# GO TOOLING (for additional developer tools)
# =============================================================================
# Some tools we might want in the future are Go-based
# Install Go for potential future tooling needs
# VERIFIED: https://go.dev/dl/ on 2025-11-27
ENV GO_VERSION="1.25.4"
RUN GOARCH=$(dpkg --print-architecture | sed 's/armhf/arm/' | sed 's/i386/386/') && \
    curl -sSL "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" -o /tmp/go.tar.gz && \
    tar -C /usr/local -xzf /tmp/go.tar.gz && \
    rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH="/go"
ENV PATH="$GOPATH/bin:$PATH"

# Install useful Go-based tools
RUN go install github.com/mikefarah/yq/v4@latest && \
    go install github.com/jesseduffield/lazygit@latest && \
    go install github.com/charmbracelet/glow@latest

# =============================================================================
# INFRASTRUCTURE & CLOUD TOOLS
# =============================================================================
# Tools for managing cloud infrastructure and secrets
# VERIFIED: 2025-11-27 from GitHub releases and official sources

# Terraform - specific version required by organization
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

# Set working directory (files copied by Cursor, not in image build)
WORKDIR /workspace

# =============================================================================
# MCP BRIDGE SETUP
# =============================================================================
# Setup MCP bridge scripts after workspace is mounted
# Note: This runs AFTER Cursor copies workspace files
# Create placeholder directory for when workspace is mounted
RUN mkdir -p /workspace/.cursor/scripts/mcp-bridge && \
    echo "# MCP bridge scripts will be available after workspace mount" > /workspace/.cursor/scripts/mcp-bridge/README.md

# =============================================================================
# FINAL VERIFICATION
# =============================================================================
# Verify all critical tools are installed and working
RUN echo "=== VERIFICATION ===" && \
    echo "Languages:" && \
    python --version && \
    node --version && \
    go version && \
    rustc --version && \
    echo "Package Managers:" && \
    pnpm --version && \
    uv --version && \
    cargo --version && \
    echo "Version Control:" && \
    git --version && \
    gh --version && \
    echo "Development Tools:" && \
    just --version && \
    sqlite3 --version && \
    rg --version && \
    fd --version && \
    jq --version && \
    ruff --version && \
    mypy --version && \
    pre-commit --version && \
    echo "Process & Browser:" && \
    process-compose version && \
    ruler --version && \
    echo "Infrastructure & Cloud:" && \
    terraform version && \
    terragrunt --version && \
    sops --version && \
    aws --version && \
    gcloud version && \
    gam version && \
    echo "=== ALL TOOLS VERIFIED ==="
