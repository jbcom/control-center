# Quick Reference: Available Tools in Background Agent Environment

## Infrastructure & Cloud Management

```bash
# Terraform
terraform version                    # Show Terraform version (1.13.1 org-specific)
terraform init                       # Initialize Terraform working directory
terraform plan                       # Preview infrastructure changes
terraform apply                      # Apply infrastructure changes

# Terragrunt
terragrunt --version                 # Show Terragrunt version (0.93.11)
terragrunt run-all plan             # Plan all modules
terragrunt run-all apply            # Apply all modules

# SOPS - Secrets Operations
sops --version                       # Show SOPS version (3.11.0)
sops -e secrets.yaml                # Encrypt file
sops -d secrets.enc.yaml            # Decrypt file
sops -i secrets.enc.yaml            # Edit encrypted file in-place

# AWS CLI
aws --version                        # Show AWS CLI version
aws s3 ls                           # List S3 buckets
aws ec2 describe-instances          # List EC2 instances
aws configure                       # Configure AWS credentials

# Google Cloud CLI
gcloud version                       # Show gcloud version (512.1.0)
gcloud auth login                   # Authenticate with Google Cloud
gcloud projects list                # List GCP projects
gsutil ls                           # List Cloud Storage buckets

# GAM - Google Workspace Management
gam version                         # Show GAM version (7.29.01)
gam info user user@example.com     # Get user information
gam print users                     # List all users
gam create user                     # Create new user
```

## Core Languages & Runtimes

```bash
python --version        # Python 3.13
node --version          # Node.js 24
rustc --version         # Rust (stable)
go version             # Go 1.23.4
```

## Package Managers

```bash
uv --version           # Python package manager (preferred)
pip --version          # Python package installer
poetry --version       # Alternative Python package manager
pnpm --version         # Node.js package manager (9.15.0)
cargo --version        # Rust package manager
go mod               # Go modules
```

## Code Search & Analysis

```bash
rg "pattern"                          # ripgrep - Fast recursive search
rg -t py "pattern"                    # Search only Python files
rg -A 3 -B 3 "pattern"               # Show 3 lines context

fd "pattern"                         # Modern find - Fast file search
fd -e py                             # Find all .py files
fd -t f -t d                         # Find files and directories

ast-grep                             # Structural code search (AST-based)

bat filename.py                      # Syntax-highlighted cat
bat -l python                        # Force Python syntax
```

## Git Operations

```bash
git status                           # Standard git
git lfs ls-files                     # List LFS files (as pointers)

gh pr list                           # GitHub CLI - List PRs
gh pr create                         # Create PR
gh pr merge 123 --squash             # Merge PR
gh run list                          # List workflow runs

delta                                # Beautiful git diffs (pipe git diff to delta)
lazygit                             # Interactive git TUI
```

## Python Development

```bash
# Testing
pytest                               # Run tests
pytest -v --cov=src                  # With coverage
pytest -x                            # Stop on first failure
pytest -k "test_name"               # Run specific test

# Type Checking
mypy src/                            # Type check with mypy
pyright src/                         # Type check with pyright

# Linting & Formatting
ruff check .                         # Check for issues
ruff check --fix .                   # Fix auto-fixable issues
ruff format .                        # Format code

# Pre-commit
pre-commit run --all-files          # Run all hooks
pre-commit install                   # Install git hooks

# Versioning
pycalver bump                        # Bump CalVer version
```

## Node.js Development

```bash
pnpm install                         # Install dependencies
pnpm run dev                         # Run dev server (don't use in background agent!)
pnpm test                            # Run tests
pnpm dlx playwright test            # Run Playwright tests
```

## Data Processing

```bash
# JSON
cat file.json | jq '.'              # Pretty-print JSON
cat file.json | jq '.key'           # Extract key
cat file.json | jq '.[] | select(.type == "foo")'  # Filter

# YAML
yq eval '.' file.yaml               # Pretty-print YAML
yq eval '.key' file.yaml            # Extract key
yq eval '.key = "value"' -i file.yaml  # Update in-place

# SQLite (for ConPort)
sqlite3 context_portal/context.db   # Open database
sqlite3 db.db "SELECT * FROM table;" # Run query
sqlite3 db.db ".schema"             # Show schema
sqlite3 db.db ".tables"             # List tables
```

## Process Management

```bash
# process-compose (orchestration)
process-compose up                   # Start all processes (foreground)
process-compose up -d                # Start in detached mode
process-compose down                 # Stop all processes
process-compose logs conport         # View logs for specific process
process-compose version              # Show version

# System processes
ps aux                               # List all processes
htop                                 # Interactive process viewer
top                                  # Classic process viewer
kill -9 PID                          # Kill process
```

## Agent Frameworks

```bash
# ConPort (context-portal-mcp)
# Usually run via process-compose, see 10-background-agent-conport.mdc for MCP tools
# Database: context_portal/context.db

# CrewAI
cd python/crew_agents
uv run crew_agents design           # Game design flow
uv run crew_agents implement        # Implementation flow
uv run crew_agents assets           # Asset generation
uv run crew_agents full             # Complete pipeline

# Ruler (agent instructions)
ruler apply                         # Apply/regenerate agent configs
ruler apply --dry-run               # Preview changes

# Aider (AI pair programming) - requires Python 3.12
aider --version                     # Check aider version
aider --model claude-haiku-4-5-20251001  # Standard model for agentic tasks
aider --no-auto-commits             # Disable auto-commits
```

## Agent Triage & Recovery

```bash
# Local triage (works without MCP)
.cursor/scripts/agent-triage-local <agent-id> analyze   # Analyze conversation
.cursor/scripts/agent-triage-local <agent-id> decompose # Create repo-specific tasks
.cursor/scripts/agent-triage-local <agent-id> execute   # Run aider analysis
.cursor/scripts/agent-triage-local <agent-id> full      # Run all phases

# Automated pipeline
.cursor/scripts/triage-pipeline     # Process all unprocessed sessions

# Memory bank replay
python scripts/replay_agent_session.py \
    --conversation .cursor/recovery/<agent-id>/conversation.json \
    --tasks-dir .cursor/recovery/<agent-id>/tasks \
    --session-label "recovered-session"

# MCP-based tools (when cursor-agent-manager running)
.cursor/scripts/mcp-bridge/cursor-agents list           # List agents
.cursor/scripts/mcp-bridge/cursor-agents status <id>    # Get agent status
.cursor/scripts/mcp-bridge/cursor-agents conversation <id>  # Get conversation

# Swarm orchestrator
.cursor/scripts/agent-swarm-orchestrator <agent-id>     # Create parallel tasks
```

## File Operations

```bash
# Modern alternatives
exa -la                             # Modern ls with icons
exa -T                              # Tree view
bat file.py                         # Syntax-highlighted cat

# Standard tools (still available)
ls -la
cat file.txt
find . -name "*.py"
grep -r "pattern"
```

## Documentation

```bash
glow README.md                      # Render markdown in terminal
glow -p README.md                   # Pager mode

vim file.txt                        # Classic editor
nano file.txt                       # Simpler editor
```

## Network & Download

```bash
curl -sSL https://example.com       # Download (silent, show errors, follow redirects)
wget https://example.com/file.zip   # Download file
```

## Task Automation

```bash
just --list                         # List available tasks (if Justfile present)
just task-name                      # Run task

make                                # Run Makefile (if present)
make test

nox                                 # Run nox sessions (if noxfile.py present)
nox -s tests
```

## Compression

```bash
unzip file.zip                      # Extract zip
zip -r archive.zip dir/             # Create zip

tar -xzf file.tar.gz               # Extract tar.gz
tar -czf archive.tar.gz dir/       # Create tar.gz
```

## Environment Info

```bash
# Paths
echo $PATH
echo $PYTHONPATH
echo $CARGO_HOME
echo $GOPATH
echo $PNPM_HOME

# Python
which python
python -c "import sys; print(sys.path)"

# Node.js
which node
which pnpm

# Workspace
echo $CONPORT_WORKSPACE_ID         # Should be /workspace
pwd                                # Current directory
```

## Common Workflows

### Search for code pattern
```bash
rg "TODO" --type py              # Find TODOs in Python files
rg -l "import requests"          # List files importing requests
fd -e py -x cat {}              # Cat all Python files
```

### Run full Python test suite
```bash
pytest -v --cov=src --cov-report=term-missing
```

### Check code quality
```bash
ruff check src/ tests/
mypy src/
pyright src/
```

### Work with ConPort database
```bash
sqlite3 context_portal/context.db ".tables"
sqlite3 context_portal/context.db "SELECT * FROM decisions LIMIT 5;"
```

### Check git status and create PR
```bash
git status
git add -A
git commit -m "feat: description"
git push -u origin branch-name
gh pr create --title "Title" --body "Description"
```

### Process management
```bash
process-compose up -d            # Start background services
process-compose logs conport     # Check ConPort logs
process-compose down             # Stop all services
```

## Debugging Tips

### Tool not found?
```bash
which tool-name                  # Find tool location
echo $PATH                       # Check PATH
command -v tool-name            # Alternative check
```

### Python import issues?
```bash
python -c "import sys; print('\n'.join(sys.path))"
uv pip list                     # List installed packages
pip show package-name           # Show package info
```

### Process issues?
```bash
htop                            # Interactive viewer
ps aux | grep process-name      # Find specific process
kill -9 $(pgrep process-name)  # Kill by name
```

## Quick Tips

1. **Use modern tools first**: `rg` instead of `grep`, `fd` instead of `find`, `bat` instead of `cat`
2. **Pipe for power**: `fd -e py | xargs bat` (syntax-highlight all Python files)
3. **Type-specific search**: `rg -t py "pattern"` (search only Python files)
4. **Interactive when needed**: `lazygit` for complex git, `htop` for processes
5. **Check versions**: All tools support `--version` or `-v` for debugging

## Tool Versions (Pinned)

```
Python:       3.13
Node.js:      24
pnpm:         9.15.0
Playwright:   1.49.0
process-compose: 1.27.0
Go:           1.23.4
Rust:         stable (via rustup)
```

## Further Reading

- Python dev: `/workspace/pyproject.toml`
- Node.js: Search for `package.json` files
- Agent rules: `/workspace/.cursor/rules/`
- ConPort: `/workspace/.cursor/rules/10-background-agent-conport.mdc`
- Environment analysis: `/workspace/.cursor/ENVIRONMENT_ANALYSIS.md`

---

**Last Updated**: 2025-11-27
**Environment**: jbcom-control-center background agent
**Docker Image**: Built from `/workspace/.cursor/Dockerfile`
