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

# ============================================
# Global Node.js CLI Tools
# These are installed globally via pnpm for all future agents
# ============================================

# Global Node.js tools - version pinned for reproducible builds
# - Ruler: AI agent instruction management
# - Claude Code: Anthropic's AI coding assistant CLI
RUN pnpm add -g @intellectronica/ruler@^1.0.0 @anthropic-ai/claude-code@^0.2.0 && \
    ruler --version && \
    (claude --version || echo "Claude installed (requires API key for full verification)")

# ============================================
# AI CLI Tools (Python-based)
# ============================================

# aider requires Python 3.12 (not 3.13) - use uv's managed Python
# See: https://github.com/Aider-AI/aider/issues/3037
ENV PATH="/root/.local/bin:$PATH"
RUN uv tool install --python python3.12 aider-chat==0.86.1 && \
    aider --version

# ============================================
# Verification - Ensure all tools are available
# ============================================
RUN echo "=== Tool Verification ===" && \
    echo "Node.js: $(node --version)" && \
    echo "Python: $(python --version)" && \
    echo "pnpm: $(pnpm --version)" && \
    echo "uv: $(uv --version)" && \
    echo "gh: $(gh --version | head -1)" && \
    echo "ruler: $(ruler --version 2>&1 | head -1)" && \
    echo "claude: $(claude --version 2>&1 | head -1 || echo 'installed, needs API key')" && \
    echo "aider: $(aider --version 2>&1 | head -1)" && \
    echo "process-compose: $(process-compose version 2>&1 | head -1)" && \
    echo "=== Verification Complete ==="
