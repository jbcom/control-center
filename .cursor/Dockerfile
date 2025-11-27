# Pre-built image with Python 3.13 + Node.js 24
# https://github.com/nikolaik/docker-python-nodejs
FROM nikolaik/python-nodejs:python3.13-nodejs24

WORKDIR /workspace

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

RUN git lfs install --system --skip-smudge

ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && \
    corepack prepare pnpm@9.15.0 --activate && \
    pnpm --version

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/F1bonacc1/process-compose/main/scripts/get-pc.sh)" -- -b /usr/local/bin && \
    process-compose version

# AI CLI Tools
# aider requires Python 3.12 (not 3.13) - use uv's managed Python
# See: https://github.com/Aider-AI/aider/issues/3037
ENV PATH="/root/.local/bin:$PATH"
RUN uv tool install --python python3.12 aider-chat==0.86.1 && \
    aider --version
