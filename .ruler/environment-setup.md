# Development Environment Setup Guide for Agents

## 🚨 CRITICAL: Use uvx and pre-commit

**NEVER try to import Python packages directly in the shell. Use `uvx` instead.**

```bash
# ❌ WRONG - Will fail with ModuleNotFoundError
python -c "import yaml; ..."
python -c "from ruamel.yaml import YAML; ..."

# ✅ CORRECT - Use uvx to run Python tools
uvx yamllint file.yml
uvx ruff check .
uvx black --check .
uvx mypy .
```

**ALWAYS use pre-commit to validate files:**

```bash
# ✅ CORRECT - Use pre-commit for validation
uvx pre-commit run --files path/to/file.yml
uvx pre-commit run yamllint --files .github/workflows/ci.yml
uvx pre-commit run ruff --files packages/
uvx pre-commit run --all-files  # Run all hooks on all files
```

`uvx` automatically installs and runs Python tools in isolated environments. This is the ONLY way to run Python tools in this workspace.

---

## Overview

This workspace can run in **TWO DIFFERENT ENVIRONMENTS**:

1. **Cursor Environment** - Dockerized environment for Cursor IDE background agents
2. **GitHub Actions Environment** - Native Ubuntu runners for CI/CD workflows

**CRITICAL:** You must understand which environment you're in and adapt accordingly.

---

## Environment Detection

Check your environment:

```bash
# Are we in Docker (Cursor)?
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Cursor Docker environment"
else
    echo "🔧 Running in GitHub Actions or native environment"
fi
```

---

## 1. Cursor Docker Environment

### What's Pre-installed

The `.cursor/Dockerfile` provides:
- **Languages:** Python 3.13, Node.js 24
- **Package Managers:** uv (Python), pnpm (Node.js)
- **System Tools:** git, gh CLI, just, sqlite3, ripgrep, fd, jq, vim, nano
- **Build Tools:** gcc, make, pkg-config (for native modules)

### What's NOT Pre-installed

**You must install these yourself when needed:**
- Python packages (use `uv sync`)
- Node.js packages (use `pnpm install`)
- Any application-specific tools (ruler, mcp-proxy, playwright, etc.)

### How to Set Up Workspace

**Option 1: Automatic with direnv**
```bash
# Install direnv if not available (unlikely in Docker)
direnv allow
# This automatically runs .envrc which:
# - Creates Python venv with UV
# - Installs Python dev dependencies
# - Installs Node.js dependencies
# - Sets up PATH
```

**Option 2: Manual Setup**
```bash
# Python environment
uv sync --extra dev --all-extras
source .venv/bin/activate

# Node.js environment  
pnpm install
export PATH="$PWD/node_modules/.bin:$PATH"
```

### Installing Additional Tools

**Node.js tools from package.json:**
```bash
# Tools are defined in package.json devDependencies
# After pnpm install, they're available in node_modules/.bin/

# Example: Run ruler
pnpm exec ruler --version
# or
./node_modules/.bin/ruler --version
```

**One-off Node.js tools:**
```bash
# Use pnpm dlx (like npx) for tools not in package.json
pnpm dlx playwright@latest install chromium
```

**Python tools:**
```bash
# Install additional Python tools if needed
uv add --dev some-tool
# or use uvx for one-off commands
uvx ruff check .
```

---

## 2. GitHub Actions Environment

### What's Pre-installed

GitHub-hosted runners come with:
- Python (multiple versions available via actions/setup-python)
- Node.js (multiple versions available via actions/setup-node)
- Common tools: git, curl, wget, jq, etc.

See full list: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2204-Readme.md

### What You Must Install

**EVERYTHING** workspace-specific:
- uv (via `astral-sh/setup-uv@v7`)
- pnpm (via corepack)
- Python dependencies (via `uv sync`)
- Node.js dependencies (via `pnpm install`)
- Any application tools

### Workflow Pattern

Our CI workflows follow this pattern:

```yaml
- uses: actions/checkout@v4

# Set up UV (for Python)
- uses: astral-sh/setup-uv@v7

# Set up pnpm (for Node.js)
- run: corepack enable && corepack prepare pnpm@9.15.0 --activate

# Install tox for testing
- run: uv tool install tox --with tox-uv --with tox-gh

# Install Node.js dependencies
- run: pnpm install

# Run tests (per-package in CI matrix)
- run: tox -e ${{ matrix.package }}
- run: pnpm exec ruler apply
```

---

## Understanding Package Management

### Python with UV (Similar to Rust's Cargo)

**pyproject.toml** = Manifest file
- Defines project metadata
- Lists dependencies
- Defines workspace members (`packages/*`)
- Dev dependencies in `[project.optional-dependencies.dev]`

**uv.lock** = Lock file (COMMITTED)
- Pins exact versions for reproducibility
- Like `Cargo.lock` or `pnpm-lock.yaml`

**Commands:**
```bash
# Install everything (respects uv.lock)
uv sync --extra dev

# Add a dependency
uv add requests

# Add a dev dependency  
uv add --dev pytest

# Run a command in the venv
uv run pytest

# Run a one-off tool without installing
uvx ruff check .
```

### Node.js with pnpm (Workspace-aware)

**package.json** = Manifest file
- Defines project metadata
- Lists devDependencies (tools like ruler, playwright)
- Specifies `packageManager: "pnpm@9.15.0"`

**pnpm-workspace.yaml** = Workspace configuration
- Can define multiple packages (currently none)
- Similar to UV's workspace concept

**pnpm-lock.yaml** = Lock file (COMMITTED)
- Pins exact versions
- Like `uv.lock`

**.npmrc** = pnpm configuration
- Workspace settings
- Registry configuration

**Commands:**
```bash
# Install everything (respects pnpm-lock.yaml)
pnpm install

# Add a dev dependency
pnpm add -D some-tool

# Run a tool from node_modules/.bin
pnpm exec ruler apply

# Run a one-off tool without installing
pnpm dlx playwright@latest install chromium
```

---

## Common Tasks by Environment

### Installing Ruler (Agent Instruction Tool)

**Cursor Docker:**
```bash
# Ruler is in package.json devDependencies
pnpm install
pnpm exec ruler --version
```

**GitHub Actions:**
```yaml
- name: Install ruler
  run: |
    corepack enable
    corepack prepare pnpm@9.15.0 --activate
    pnpm install
    pnpm exec ruler --version
```

### Running Tests

**Cursor Docker:**
```bash
# Install tox with uv backend
uv tool install tox --with tox-uv --with tox-gh
export PATH="$HOME/.local/bin:$PATH"

# Run all package tests
tox -e extended-data-types,lifecyclelogging,directed-inputs-class,python-terraform-bridge,vendor-connectors

# Run single package
tox -e extended-data-types

# Run lint
tox -e lint
```

**GitHub Actions:**
```yaml
- uses: astral-sh/setup-uv@v7
- run: uv tool install tox --with tox-uv --with tox-gh
- run: tox -e ${{ matrix.package }}
```

### Installing Playwright

**Cursor Docker:**
```bash
# One-time browser installation
pnpm dlx playwright@1.49.0 install chromium

# Or if you need it frequently, add to package.json:
pnpm add -D playwright
pnpm exec playwright install chromium
```

**GitHub Actions:**
```yaml
- name: Install Playwright
  run: |
    pnpm add -D playwright
    pnpm exec playwright install chromium --with-deps
```

---

## When You Need a Tool

### Decision Tree:

1. **Is it a Python tool for development?**
   - Add to `pyproject.toml` under `[project.optional-dependencies.dev]`
   - Run `uv sync --extra dev`

2. **Is it a Node.js tool for development?**
   - Add to `package.json` under `devDependencies`
   - Run `pnpm install`

3. **Is it a system tool everyone needs?**
   - Add to `.cursor/Dockerfile` (system packages via apt)
   - Document requirement for GitHub Actions in workflow

4. **Is it a one-off tool?**
   - Use `uvx` (Python) or `pnpm dlx` (Node.js)
   - Don't install globally

### Examples:

**Python formatting with Ruff:**
```bash
# Already in package.json dev deps
uv run ruff check .
uv run ruff format .
```

**TypeScript type checking:**
```bash
# Add if not present
pnpm add -D typescript
pnpm exec tsc --noEmit
```

**Running a script:**
```bash
# Python script
uv run python scripts/my_script.py

# Node.js script  
pnpm exec ts-node scripts/my_script.ts
```

---

## Environment Variables

Both environments should respect:

```bash
# Python
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Telemetry
export DO_NOT_TRACK=1
export DISABLE_TELEMETRY=1

# Package managers
export UV_LINK_MODE=copy  # For UV
export PNPM_HOME=/root/.local/share/pnpm  # For pnpm
```

These are set in:
- `.cursor/Dockerfile` (for Cursor environment)
- `.envrc` (for direnv users)
- Workflows (for GitHub Actions)

---

## Troubleshooting

### "Command not found: ruler"

**Cursor:** Run `pnpm install` first
**GitHub Actions:** Add pnpm setup to workflow

### "Module not found: extended_data_types"

**Both:** Run `uv sync` to install workspace packages

### "ENOENT: no such file or directory, open 'pnpm-lock.yaml'"

**Both:** Run `pnpm install` to generate lock file

### "uv: command not found"

**Cursor:** Should never happen (pre-installed in Dockerfile)
**GitHub Actions:** Add `uses: astral-sh/setup-uv@v7` to workflow

---

## Best Practices

1. **Always use lock files**
   - Commit `uv.lock` and `pnpm-lock.yaml`
   - Never use `--no-lock` or `--frozen-lockfile` unless necessary

2. **Use workspace dependencies**
   - Python packages reference each other via `{ workspace = true }`
   - This ensures you're testing against local code, not PyPI

3. **Prefer workspace tools over global**
   - Don't install tools globally in Dockerfile
   - Define them in package.json/pyproject.toml
   - This makes dependencies explicit and version-controlled

4. **Document new requirements**
   - Update this file when adding new tools
   - Update Dockerfile if system packages needed
   - Update CI workflows if new setup steps required

---

## Quick Reference

### Cursor Docker Environment
```bash
# Setup
uv tool install tox --with tox-uv --with tox-gh
export PATH="$HOME/.local/bin:$PATH"
pnpm install

# Run tests (all packages)
tox -e extended-data-types,lifecyclelogging,directed-inputs-class,python-terraform-bridge,vendor-connectors

# Run single package tests
tox -e extended-data-types

# Lint
tox -e lint

# Other tools
pnpm exec ruler apply
```

### GitHub Actions
```yaml
# Setup
- uses: astral-sh/setup-uv@v7
- run: uv tool install tox --with tox-uv --with tox-gh
- run: corepack enable && corepack prepare pnpm@9.15.0 --activate
- run: pnpm install

# Use
- run: tox -e ${{ matrix.package }}
- run: pnpm exec ruler apply
```

### Adding Dependencies
```bash
# Python
uv add requests              # Production
uv add --dev pytest-cov      # Development

# Node.js
pnpm add axios               # Production
pnpm add -D typescript       # Development
```
