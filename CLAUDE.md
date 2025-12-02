

<!-- Source: .ruler/AGENTS.md -->

# AI Agent Guidelines for Unified Control Center

**Single control surface for jbcom +  ecosystems.**

## 🚨 MANDATORY FIRST: SESSION START

### Session Start Checklist:
```bash
# 1. Read core agent rules
cat .ruler/AGENTS.md
cat ECOSYSTEM.toml

# 2. Check active GitHub Issues for context
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list --label "agent-session" --state open

# 3. Check your fleet tooling
agentic fleet list --running
```

### Your Tools:
| Tool | Command | Purpose |
|------|---------|---------|
| Fleet management | `agentic fleet list/spawn/followup` | Manage Cursor background agents |
| Fleet coordination | `agentic fleet coordinate --pr N` | Bidirectional agent coordination |
| Triage | `agentic triage analyze <session>` | AI-powered session analysis |
| GitHub | `agentic github pr/issue` | Token-aware GitHub operations |

## 🔑 CRITICAL: Authentication

**Token switching is AUTOMATIC based on repository organization:**
```bash
# jbcom repos → uses GITHUB_JBCOM_TOKEN
agentic github pr create --repo jbcom/extended-data-types

#  repos → uses GITHUB_FSC_TOKEN
agentic github pr create --repo /terraform-modules

# PR reviews ALWAYS use GITHUB_JBCOM_TOKEN
```

**Manual operations:**
```bash
# jbcom
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...

# 
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr create ...
```

## 📦 Repository Structure

### jbcom Ecosystem (Python/Node.js Packages)
```
packages/
├── extended-data-types/      # Foundation (Python → PyPI)
├── lifecyclelogging/         # Logging (Python → PyPI)
├── directed-inputs-class/    # Validation (Python → PyPI)
├── python-terraform-bridge/  # Terraform utils (Python → PyPI)
├── vendor-connectors/        # Cloud SDKs (Python → PyPI)
└── agentic-control/          # Agent orchestration (Node.js → npm)
```

###  Ecosystem (Infrastructure)
```
ecosystems//
├── terraform/
│   ├── modules/              # 100+ reusable modules
│   │   ├── aws/              # AWS (70+ modules)
│   │   ├── google/           # GCP (38 modules)
│   │   └── github/           # GitHub management
│   └── workspaces/           # 44 live workspaces
│       ├── terraform-aws-organization/
│       └── terraform-google-organization/
├── sam/                      # AWS Lambda apps
├── lib/                      # Python libraries
├── config/                   # State paths, pipelines
└── memory-bank/              # Agent context
```

## 🚀 CI/CD & Release Workflow

### How Releases Actually Work

**This repo uses Python Semantic Release (PSR) with SemVer (`MAJOR.MINOR.PATCH`).**

#### Version Format
- Format: `MAJOR.MINOR.PATCH` (standard SemVer)
- Driven by conventional commits with package scopes
- Each package has its own independent version and tag

#### Conventional Commit Scopes
| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `bridge` or `ptb` | python-terraform-bridge |
| `connectors` | vendor-connectors |

#### Example Commits
```bash
feat(dic): add decorator-based input handling   # → directed-inputs-class minor bump
fix(bridge): resolve command injection issue    # → python-terraform-bridge patch bump
feat(connectors): add S3 bucket operations      # → vendor-connectors minor bump
```

#### Release Flow
```
Push to main with conventional commit
  ↓
CI runs tests & lint
  ↓
PSR analyzes commits per package (path-filtered)
  ↓
Version bumped in pyproject.toml + __init__.py
  ↓
Git tag created (e.g., python-terraform-bridge-v202511.2.0)
  ↓
Package built and published to PyPI
  ↓
Synced to public repo (e.g., jbcom/python-terraform-bridge)
```

### Package Configuration

Each package has PSR config in `pyproject.toml`:
```toml
[tool.semantic_release]
build_command = "pip install uv && uv build"
commit_parser = "../../scripts/psr/monorepo_parser.py:ConventionalCommitMonorepoParser"
tag_format = "package-name-v{version}"
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/package_name/__init__.py:__version__"]

[tool.semantic_release.commit_parser_options]
path_filters = ["packages/package-name/*"]
scope_prefix = "scope"
```

### CI Workflow Matrix

The `.github/workflows/ci.yml` has these jobs:
1. **build-packages** - Build all packages
2. **tests** - Run pytest for each package (py3.9 + py3.13)
3. **lint** - Ruff check and format
4. **release** - PSR version bump + PyPI publish + public repo sync
5. **docs** - Build and deploy documentation

## 🎯 PR Ownership Rule

**First agent on PR = PR Owner**
- Handle ALL feedback (from @gemini-code-assist, @copilot, etc.)
- Resolve AI-to-AI conflicts yourself
- Merge when CI passes and feedback addressed

## 🔍 MANDATORY: AI QA Review Before Merge

**NEVER merge without engaging AI reviewers and addressing ALL feedback.**

### How to Request Review

**Comment-triggered** (post as PR comment):
```
/gemini review       # Google Gemini Code Assist
/q review            # Amazon Q Developer
@copilot review      # GitHub Copilot
@cursor review       # Cursor AI
@coderabbitai review # CodeRabbit AI review
```

**Automatic** (via repo settings):
- Copilot - Enable in Settings > Code security and analysis
- Cursor Bugbot - Automatic on all PRs

### Scope
- **Required**: All code changes, bug fixes, features, refactors, API changes, config changes affecting runtime
- **Not Required**: Pure documentation changes (README, comments only), whitespace/formatting-only, automated Dependabot bumps with no code changes

### Merge Checklist

Before merging ANY PR:
- [ ] CI is green (all checks pass)
- [ ] At least ONE AI review requested and completed
- [ ] ALL critical/high severity items resolved (fixed OR documented as false positive)
- [ ] ALL medium items resolved or justified with technical reasoning
- [ ] Responses posted to ALL feedback items
- [ ] All review threads addressed
- [ ] AI-to-AI conflicts resolved and documented

### Addressing Feedback by Severity

- 🛑 **Critical/High** - MUST be resolved before merge (fix OR document false positive)
- ⚠️ **Medium** - Should be resolved or provide strong justification
- 💡 **Low/Info** - Consider, document if skipping

Actions:
1. **Fix** the issue, OR
2. **Reply** with technical justification for disagreeing
3. **NEVER** ignore or dismiss without response
4. **Re-request** review after significant changes

### Resolving AI Conflicts
When AI reviewers disagree:
- Evaluate both positions for technical merit
- Apply project conventions as tiebreaker
- Document your decision and reasoning
- Prefer security/correctness when in doubt
- Escalate to team lead if genuinely ambiguous

### Automatic AI Review (Repo Settings)
Enable in **Settings > Code security and analysis > Copilot code review** for automatic Copilot reviews on all PRs. See `.cursor/rules/15-ai-qa-engagement.mdc` for full setup guide

## 📝 Making Changes

### Adding a New Package to CI

To add a package to CI releases:
1. Add PSR config to package's `pyproject.toml`
2. Add `__version__` to package's `__init__.py`
3. Create public repo (e.g., `jbcom/package-name`)
4. Add to `.github/workflows/ci.yml` matrices:
   - `build-packages.matrix.package`
   - `tests.matrix.package`
   - `release.matrix.include` (with repo)
   - `docs.matrix.include` (with repo)

### Local Development
```bash
# Install tox (CI-consistent testing)
uv tool install tox --with tox-uv --with tox-gh
export PATH="$HOME/.local/bin:$PATH"

# Run tests for a package
tox -e directed-inputs-class

# Run all package tests
tox -e extended-data-types,lifecyclelogging,directed-inputs-class,python-terraform-bridge,vendor-connectors

# Run lint
tox -e lint
```

### Creating PRs
1. Create feature branch
2. Make changes with conventional commits
3. Run tests locally
4. Create PR against `main`
5. CI runs automatically
6. Address feedback
7. Merge when ready

## 🤖 Agent Behavior

### Background Agent Rules
1. **DO** create PRs and iterate on feedback
2. **DO** run CI and fix failures
3. **DO** use conventional commits with scopes
4. **WAIT** for approval unless user says "merge it"

### When User Says "merge it", "go ahead":
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUMBER> --squash --delete-branch
```

## 🔧 Fleet Management

### Spawn Sub-Agents
```bash
# Spawn agent in another repo (auto-selects token based on org)
agentic fleet spawn "https://github.com/jbcom/vendor-connectors" "Fix CI failures" --ref main

# For  repos (also uses GITHUB_FSC_TOKEN automatically)
agentic fleet spawn "https://github.com//cluster-ops" "Complete PR" --ref proposal/vault-secret-sync

# Send followup to running agent
agentic fleet followup <agent-id> "Update: ..."

# Monitor agents
agentic fleet list --running

# Check which token will be used for a repo
agentic tokens for-repo /cluster-ops
```

### Bidirectional Coordination
```bash
# Start coordinator (uses PR for communication)
agentic fleet coordinate --pr 251 --repo jbcom/jbcom-control-center
```

### AI Triage & Analysis
```bash
# Analyze agent session
agentic triage analyze <agent-id> --output report.md

# Code review
agentic triage review --base main --head HEAD
```

---

**Last Updated:** 2025-11-30
**Versioning:** SemVer via python-semantic-release (per-package)
**Status:** Production monorepo for jbcom ecosystem



<!-- Source: .ruler/agent-self-sufficiency.md -->

# Agent Self-Sufficiency Rules

**CRITICAL: Read this when you encounter "command not found" or missing tools**

## Core Principle: Tools Should Exist, Use Them

If you encounter a missing tool or command, it usually means ONE of three things:

1. **Tool is in Dockerfile but environment not rebuilt** → Document for user
2. **Tool should be in Dockerfile but isn't** → ADD IT
3. **Tool is non-standard and shouldn't be assumed** → Use alternatives

## Decision Tree: Missing Tool

```
Tool not found
    ↓
Is tool listed in .cursor/TOOLS_REFERENCE.md?
    ├─ YES → Environment needs rebuild
    │         → Document in PR/commit: "Requires Docker rebuild"
    │         → Continue with workarounds if possible
    │
    └─ NO → Should this tool be available?
              ├─ YES → ADD to Dockerfile immediately
              │         → Common tools (see list below)
              │         → Document why it's needed
              │
              └─ NO → Use standard alternatives
                        → python/node/rust/go standard library
                        → Tools already in environment
```

## Common Tools That MUST Be Available

### Always Available (Core System)
```bash
# These should ALWAYS work
python --version
node --version  
git --version
bash --version
sh --version
```

### Should Be Available (In Dockerfile)
```bash
# Package managers
pip, uv, pnpm, cargo, go

# Code search
rg (ripgrep), fd, ast-grep

# Data processing  
jq, yq, sqlite3

# Git operations
git, git-lfs, gh, delta, lazygit

# Process management
process-compose, htop, ps, top

# Text processing
bat, exa, vim, nano

# Development
pytest, mypy, ruff, pre-commit

# Agent tools
ruler (for applying agent config changes)
```

### Never Assume Available
```bash
# Don't assume these exist
docker (we're INSIDE docker)
kubectl, helm (cluster tools)
aws, gcloud, az (cloud CLIs - use vendor-connectors)
terraform, pulumi (IaC tools)
```

## When to Add Tools to Dockerfile

### ✅ ADD IMMEDIATELY
- **Standard development tools** everyone needs
- **Security tools** for vulnerability scanning
- **Performance tools** for profiling/debugging
- **Agent management tools** (ruler, etc.)
- **Tools required by project rules** (ripgrep is REQUIRED per .cursorrules)

### ⚠️ ADD WITH JUSTIFICATION
- **Language-specific tools** (add to appropriate section)
- **Build tools** for specific frameworks
- **Testing tools** beyond pytest
- **Database clients** beyond sqlite3

### ❌ DON'T ADD
- **Project-specific tools** (install via package.json/pyproject.toml)
- **One-off utilities** (download in CI or use alternatives)
- **Deprecated tools** (find modern alternatives)
- **Redundant tools** (if we have ripgrep, don't add grep alternatives)

## How to Add Tools to Dockerfile

### Pattern 1: System Package (apt)
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tool-name \
    && rm -rf /var/lib/apt/lists/*
```

**Examples**: jq, vim, htop, ripgrep

### Pattern 2: Python Package (pip)
```dockerfile
RUN pip install --no-cache-dir \
    package-name>=X.Y.Z
```

**Examples**: pytest, mypy, ruff

### Pattern 3: Node.js Package (pnpm)
```dockerfile
RUN pnpm install -g \
    package-name
```

**Examples**: @intellectronica/ruler, typescript

### Pattern 4: Rust Tool (cargo)
```dockerfile
RUN cargo install --locked \
    tool-name \
    && rm -rf $CARGO_HOME/registry
```

**Examples**: ripgrep, fd-find, bat, exa

### Pattern 5: Go Tool (go install)
```dockerfile
RUN go install github.com/user/tool@latest
```

**Examples**: yq, lazygit, glow

### Pattern 6: Binary Download
```dockerfile
ENV TOOL_VERSION="vX.Y.Z"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/user/tool/releases/download/${TOOL_VERSION}/tool-linux-${ARCH}" \
    -o /usr/local/bin/tool && \
    chmod +x /usr/local/bin/tool && \
    tool --version
```

**Examples**: process-compose

## Update Dockerfile Process

When you add a tool:

1. **Choose the right section** in Dockerfile
2. **Add with comment** explaining why
3. **Verify in verification step** at end of Dockerfile
4. **Update TOOLS_REFERENCE.md** with usage examples
5. **Update ENVIRONMENT_ANALYSIS.md** if significant
6. **Document in PR** that Docker rebuild required

### Example: Adding jq (already done correctly)

```dockerfile
# In SYSTEM DEPENDENCIES section
RUN apt-get update && apt-get install -y --no-install-recommends \
    # ... other tools ...
    # JSON/YAML processing
    jq \
    # ... more tools ...
```

```dockerfile
# In FINAL VERIFICATION section  
RUN echo "=== VERIFICATION ===" && \
    # ... other checks ...
    jq --version && \
    # ... more checks ...
```

### Example: Adding ruler (just added)

```dockerfile
# In NODE.JS GLOBAL TOOLS section
RUN pnpm install -g \
    # Ruler - Agent instruction management
    @intellectronica/ruler \
    && ruler --version
```

## Workarounds When Tool Unavailable

### If jq not available
```bash
# Use python instead
python -c "import json, sys; print(json.load(sys.stdin)['key'])" < file.json

# Or for GitHub API
gh api endpoint --jq '.key'  # gh has built-in jq
```

### If yq not available
```bash
# Use python with ruamel.yaml
python -c "import sys; from ruamel.yaml import YAML; yaml=YAML(); print(yaml.load(sys.stdin)['key'])" < file.yaml
```

### If ripgrep not available
```bash
# Fallback to grep (much slower)
grep -r "pattern" .

# But really, add ripgrep - it's REQUIRED by rules
```

### If ruler not available
```bash
# Manual concatenation (not ideal)
cat .ruler/AGENTS.md .ruler/copilot.md .ruler/cursor.md > .cursorrules

# But really, just add ruler to Dockerfile
```

## Self-Healing: Apply Your Own Changes

When you identify a missing tool:

1. **Add it to Dockerfile** immediately (this PR or next commit)
2. **Update documentation** (TOOLS_REFERENCE.md)
3. **Apply agent config changes** with ruler (see below)
4. **Note in commit message**: "Adds <tool> to environment (discovered missing during <task>)"
5. **Verify addition** in verification step
6. **Test locally if possible** or note that rebuild required

### Applying Agent Configuration Changes

**CRITICAL: Cursor reads from `.cursor/rules/*.mdc` files, NOT `.cursorrules`**

When you update agent rules in `.ruler/*.md`:

```bash
# Apply ruler to regenerate all agent configs
ruler apply

# This updates:
# - .cursorrules (for legacy Cursor)
# - .github/copilot-instructions.md (for Copilot)  
# - AGENTS.md (for Aider)
# - .claud (for Claude)
```

**For Cursor background agent, edit these directly:**
- `.cursor/rules/00-loader.mdc` - Project structure and workflow
- `.cursor/rules/05-pr-ownership.mdc` - PR collaboration protocol
- `.cursor/rules/10-background-agent-conport.mdc` - Memory management

**Cursor loads `.mdc` files automatically - no regeneration needed!**

### Example Commit Message
```
build: add ruler to Docker environment

Discovered during PR workflow when attempting to apply agent config
changes. Ruler is essential for maintaining .cursorrules and other
agent-specific configs.

Added as Node.js global via pnpm in NODE.JS GLOBAL TOOLS section.

Requires Docker rebuild: docker build -f .cursor/Dockerfile .
```

## Documentation Updates

When adding tools, update:

### .cursor/TOOLS_REFERENCE.md
```markdown
## New Tool Section

\`\`\`bash
tool-name command            # Description
tool-name --help             # Show help
\`\`\`

### Common Workflows
- Use case 1
- Use case 2
```

### .cursor/ENVIRONMENT_ANALYSIS.md
If significant addition:
```markdown
## Tool Requirements (Update)

### New Category
**New tool** (added YYYY-MM-DD)
- Purpose: Why it's needed
- Installation: How it's installed
- Workflow: What workflow it supports
```

## Anti-Patterns

### ❌ Silently Fail
```bash
# Bad: Silently skip if tool missing
which tool && tool command || echo "Skipped"

# Good: Fail explicitly
if ! which tool > /dev/null; then
    echo "ERROR: tool not found. Add to .cursor/Dockerfile"
    exit 1
fi
```

### ❌ Install Locally
```bash
# Bad: Install in running container (non-persistent)
apt-get install tool

# Good: Add to Dockerfile (persists across rebuilds)
# Edit .cursor/Dockerfile, document rebuild needed
```

### ❌ Assume User Has Tool
```bash
# Bad: Assume tool on user's machine
docker run --rm -v $(which tool):/usr/local/bin/tool ...

# Good: Tool should be in Docker image
# Add to Dockerfile
```

### ❌ Use Obscure Tools
```bash
# Bad: Use tool nobody has heard of
obscure-json-parser file.json

# Good: Use standard, well-known tools
jq '.' file.json
```

## Verification Checklist

Before committing Dockerfile changes:

- [ ] Tool added to appropriate section (system deps, python, node, rust, go)
- [ ] Comment explains why tool is needed
- [ ] Version pinned if critical for reproducibility
- [ ] Verification step updated (tool --version check)
- [ ] TOOLS_REFERENCE.md updated with usage
- [ ] ENVIRONMENT_ANALYSIS.md updated if significant
- [ ] Commit message notes Docker rebuild required
- [ ] PR description includes rebuild instructions

## Common Scenarios

### Scenario 1: "ruler: command not found"
**Analysis**: ruler is agent management tool, should be available
**Action**: Add to Dockerfile as Node.js global
**Documentation**: Update TOOLS_REFERENCE.md
**Result**: ✅ Done (just added)

### Scenario 2: "jq: command not found"  
**Analysis**: jq is standard JSON tool, listed in Dockerfile but not in current environment
**Action**: Document rebuild needed, continue with python fallback
**Documentation**: Note in commit/PR
**Result**: ⏳ Rebuild required

### Scenario 3: "custom-parser: command not found"
**Analysis**: Project-specific tool, not general-purpose
**Action**: Don't add to Dockerfile, install via package manager in project
**Documentation**: Add to README for that package
**Result**: ✅ Correct approach

### Scenario 4: "docker: command not found"
**Analysis**: We're inside Docker, can't use Docker
**Action**: This is expected, find alternative approach
**Documentation**: Document why Docker-in-Docker not supported
**Result**: ✅ Use different approach

## Summary

1. **Expect tools to exist** - Dockerfile should be comprehensive
2. **Add missing common tools** - Don't work around, fix root cause
3. **Document additions** - Help future agents understand why
4. **Update references** - Keep TOOLS_REFERENCE.md current
5. **Test verification** - Ensure tool checks in Dockerfile work
6. **Self-heal** - You can fix your own environment

**The agent environment should be complete enough that you rarely encounter "command not found" for standard development tasks.**

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-27  
**Related**: `.cursor/Dockerfile`, `.cursor/TOOLS_REFERENCE.md`



<!-- Source: .ruler/copilot.md -->

# GitHub Copilot Agent Configuration

Comprehensive guide for GitHub Copilot when working in jbcom ecosystem repositories.

## 🚨 CRITICAL: Read First!

### Automatic Issue Handling
When you receive an issue labeled `copilot`:
1. **Read the full issue description** carefully
2. **Check `.ruler/AGENTS.md`** for project rules
3. **Create a feature branch**: `copilot/issue-{number}-{short-description}`
4. **Implement with tests** - every feature needs tests
5. **Run verification**: `ruff check . && pytest`
6. **Create PR** linking to the issue

### Versioning & Releases
✅ Each package uses python-semantic-release (SemVer `MAJOR.MINOR.PATCH`)
✅ Conventional commits with scopes drive version bumps
❌ **NEVER** edit `__version__` or pyproject versions manually
❌ **NEVER** reintroduce alternative versioning schemes, git tag workflows, or manual bump scripts

### Release Process
✅ PSR determines if a release is needed when main is updated
✅ Approved commits trigger: version bump → tag → PyPI publish → repo sync
❌ **NEVER** suggest conditional/manual release steps outside PSR

## Working with Auto-Generated Issues

Issues created by `agentic triage analyze` have this structure:
```markdown
## Summary
[Description of the task]

## Priority
`HIGH` or `CRITICAL` or `MEDIUM` or `LOW`

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated if needed
- [ ] CI passes
```

### Your Workflow for These Issues:
1. Parse the Summary for requirements
2. Check Priority - `CRITICAL`/`HIGH` = do first
3. Complete ALL Acceptance Criteria checkboxes
4. Reference the issue number in your PR

## Repository Structure

```
jbcom-control-center/
├── packages/                    # All Python packages (monorepo)
│   ├── extended-data-types/     # Foundation library
│   ├── lifecyclelogging/        # Logging utilities
│   ├── directed-inputs-class/   # Input validation
│   ├── vendor-connectors/       # External service connectors
│   ├── agentic-control/         # Agent orchestration toolkit (Node.js)
│   └── python-terraform-bridge/ # Terraform utilities
├── .ruler/                      # Agent instructions (source of truth)
├── .github/workflows/           # CI/CD workflows
└── pyproject.toml               # Workspace configuration
```

## Code Patterns

### Python Type Hints (Required)
```python
# ✅ CORRECT - Modern type hints
from collections.abc import Mapping, Sequence
from typing import Any

def process_data(items: list[dict[str, Any]]) -> dict[str, int]:
    """Process items and return counts."""
    return {"count": len(items)}

# ❌ WRONG - Legacy typing
from typing import Dict, List
def process_data(items: Dict[str, Any]) -> List[str]:
    pass
```

### Use Pathlib (Always)
```python
# ✅ CORRECT
from pathlib import Path
config_file = Path("config.yaml")
if config_file.exists():
    content = config_file.read_text()

# ❌ WRONG
import os
config_file = os.path.join("config.yaml")
```

### Error Handling
```python
# ✅ CORRECT - Specific, helpful errors
if not config_file.exists():
    raise FileNotFoundError(
        f"Config file not found: {config_file}. "
        f"Create it with: python setup.py init"
    )

# ❌ WRONG - Vague errors
raise FileNotFoundError("Config not found")
```

## Testing Requirements

### Every Feature Needs Tests
```python
# ✅ CORRECT - Descriptive name, clear assertion
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ✅ CORRECT - Use fixtures for setup
@pytest.fixture
def sample_data():
    return [{"id": i} for i in range(10)]

def test_with_fixture(sample_data):
    result = process_data(sample_data)
    assert result["count"] == 10
```

### Test Edge Cases
- Empty inputs
- Invalid inputs (should raise appropriate errors)
- Boundary conditions
- Large inputs (if performance matters)

## Package Dependencies

### Use extended-data-types Utilities
Before adding any utility function, check if `extended-data-types` provides it:

```python
# ✅ CORRECT - Use existing utilities
from extended_data_types import (
    strtobool,              # String to boolean
    strtopath,              # String to Path
    make_raw_data_export_safe,  # Sanitize data for logging
    get_unique_signature,   # Generate unique IDs
    encode_json,            # JSON serialization
    decode_yaml,            # YAML parsing
)

# ❌ WRONG - Reimplementing existing functionality
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

### Dependency Order (for releases)
1. `extended-data-types` (foundation)
2. `lifecyclelogging` (depends on #1)
3. `directed-inputs-class` (depends on #1)
4. `vendor-connectors` (depends on #1, #2, #3)

## Security Requirements

### Never Log Secrets
```python
# ✅ CORRECT - Sanitize before logging
from extended_data_types import make_raw_data_export_safe
safe_data = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe_data}")

# ❌ WRONG - May log secrets
logger.info(f"Processing: {user_data}")
```

### Validate All Inputs
```python
# ✅ CORRECT - Validate before use
def load_config(filepath: str) -> dict[str, Any]:
    path = Path(filepath)
    if not path.is_file():
        raise ValueError(f"Not a file: {filepath}")
    if path.suffix not in (".json", ".yaml", ".yml"):
        raise ValueError(f"Unsupported format: {path.suffix}")
    return decode_yaml(path.read_text())
```

## Documentation Standards

### Google-Style Docstrings
```python
def process_items(items: list[dict], validate: bool = True) -> dict[str, Any]:
    """Process a list of items and return summary.

    Args:
        items: List of dictionaries containing item data.
        validate: Whether to validate items before processing.

    Returns:
        Dictionary with processing summary and statistics.

    Raises:
        ValueError: If items list is empty or validation fails.

    Example:
        >>> items = [{"id": 1, "name": "Item 1"}]
        >>> process_items(items)
        {"count": 1, "valid": 1}
    """
```

## PR Creation Guidelines

When creating a PR from an issue:

### Title Format
```
feat(package): Brief description (fixes #123)
```

### Body Template
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Manual testing completed
- [ ] CI passes

## Related
Fixes #123
```

### Commit Messages
```bash
# Feature
feat(extended-data-types): Add new utility function

# Bug fix
fix(vendor-connectors): Handle null response from API

# Documentation
docs(lifecyclelogging): Update README with examples

# Refactor
refactor(directed-inputs-class): Simplify validation logic
```

## Verification Before PR

Always run before creating PR:

```bash
# Python packages
cd packages/<package-name>
ruff check .
ruff format --check .
pytest

# TypeScript packages
cd packages/agentic-control
pnpm build
pnpm test  # if tests exist
```

## Common Mistakes to Avoid

### ❌ Don't Suggest Version Changes
```python
# WRONG - Never touch this manually
__version__ = "2025.11.42"  # This is auto-generated
```

### ❌ Don't Add Unnecessary Dependencies
Check `extended-data-types` first before adding:
- `inflection` - already re-exported
- `orjson` - already re-exported  
- `ruamel.yaml` - already re-exported
- Custom JSON/YAML functions - use existing

### ❌ Don't Skip Tests
Every new function needs at least:
- Happy path test
- Edge case test (empty input, invalid input)

### ❌ Don't Ignore Type Hints
```python
# WRONG - Missing type hints
def process(data):
    return data

# CORRECT
def process(data: dict[str, Any]) -> dict[str, Any]:
    return data
```

## Integration with agentic-control

If you need to understand what previous agents did:

```bash
# Analyze a previous agent session
agentic triage analyze bc-xxx-xxx --output report.md

# Review code before pushing
agentic triage review --base main --head HEAD

# Check token status
agentic tokens status
```

## Questions?

- **Project Rules**: `.ruler/AGENTS.md`
- **Ecosystem Guide**: `.ruler/ecosystem.md`
- **Template Usage**: `TEMPLATE_USAGE.md`
- **Package Details**: `packages/*/README.md`

---

**Copilot Instructions Version:** 2.0
**Auto-Issue Compatible:** Yes
**Last Updated:** 2025-11-30



<!-- Source: .ruler/cursor.md -->

# Cursor-Specific Agent Configuration

This file contains Cursor AI specific instructions not covered by standard ruler configuration.

## 🔑 CRITICAL: Authentication (READ FIRST!)

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
```

The default `GH_TOKEN` does NOT have jbcom access. NEVER use bare `gh` commands for jbcom repos.

## 🎛️ agentic-control Configuration

This workspace uses `agentic-control` for fleet management and triage. Configuration is in `/workspace/agentic.config.json`:

- **jbcom** repos → `GITHUB_JBCOM_TOKEN`
- **** repos → `GITHUB_FSC_TOKEN`
- **PR reviews** always use `GITHUB_JBCOM_TOKEN` for consistent identity

Use the CLI:
```bash
# Check token status
agentic tokens status

# Spawn agent with explicit model
agentic fleet spawn https://github.com/jbcom/repo "Task" --model claude-sonnet-4-20250514

# Analyze a session
agentic triage analyze bc-xxx-xxx -o report.md
```

## 🚨 CRITICAL: Long-Running PR Workflow for Multi-Merge Sessions

When a background agent needs to manage **multiple merges to main** and oversee **multiple CI runs**, you MUST use the following workflow pattern. Failure to do so will cause the background agent session to terminate prematurely when a PR is merged.

### The Problem

When a background agent creates a PR and merges it, the session closes because the associated branch is deleted. This prevents the agent from:
- Watching CI after the merge
- Fixing issues discovered in main branch CI
- Creating follow-up PRs
- Completing multi-step CI/CD stabilization work

### The Solution: Holding PR + Interim PRs

**ALWAYS create TWO types of branches:**

1. **Holding Branch/PR** (stays open, keeps session alive):
   ```bash
   git checkout -b agent/holding-pr-for-<task>-$(date +%Y%m%d-%H%M%S)
   # Make a small change (update agent docs, add a comment, etc.)
   git commit -m "Agent holding PR for <task>"
   git push -u origin HEAD
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "[HOLDING] Agent session for <task>" \
     --body "This PR keeps the background agent session alive. DO NOT MERGE until agent work is complete."
   ```

2. **Interim Branches/PRs** (for actual fixes, get merged):
   ```bash
   git checkout main && git pull
   git checkout -b fix/<specific-issue>
   # Make the actual fix
   git commit -m "Fix: <specific issue>"
   git push -u origin HEAD
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "Fix: <issue>"
   # After CI passes, merge it
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <PR_NUM> --squash --delete-branch
   # Watch main CI, if it fails, create another interim PR
   ```

### Complete Multi-Merge Workflow

```
1. START: Create holding branch from main
   ↓
2. Create holding PR (title: "[HOLDING] Agent session...")
   ↓
3. Switch back to main
   ↓
4. Create interim branch for first fix
   ↓
5. Create interim PR, get CI green, merge it
   ↓
6. Watch main branch CI run
   ↓
7. If CI fails → Go to step 4 with new interim branch
   ↓
8. If CI passes → Continue to next task or complete
   ↓
9. ONLY WHEN ALL DONE: Close/merge holding PR
```

### Rules for Long-Running Sessions

1. **NEVER merge the holding PR** until all work is complete
2. **ALWAYS watch main CI** after each interim PR merge
3. **Create NEW interim branches** from updated main for each fix
4. **Keep the holding PR title clear**: Use `[HOLDING]` prefix
5. **Document progress** in holding PR comments

### Example Session Flow

```bash
# 1. Create holding PR
git checkout -b agent/holding-ci-fixes-20251126
echo "# Agent Session" >> .cursor/agents/session-notes.md
git add -A && git commit -m "Agent holding PR for CI fixes"
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "[HOLDING] Agent session for CI/CD fixes"

# 2. Switch to main for actual work
git checkout main && git pull

# 3. First fix
git checkout -b fix/enforce-workflow-404-error
# ... make fix ...
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "Fix: enforce workflow 404 error"
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch

# 4. Watch CI
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/jbcom-control-center --limit 3
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run watch <RUN_ID>

# 5. If fails, repeat from step 2
git checkout main && git pull
git checkout -b fix/next-issue
# ... and so on ...

# 6. When ALL green, close holding PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr close <HOLDING_PR_NUM>
```

## Background Agent Modes

### Code Review Mode
When reviewing code in PRs:
- Focus on logic and correctness
- Check type safety
- Verify test coverage
- Look for security issues
- Don't propose manual version bumps or deviations from python-semantic-release

### Maintenance Mode
For routine maintenance tasks:
- Update dependencies
- Fix linting issues
- Improve documentation
- Refactor for clarity
- Keep it simple

### Migration Mode
When migrating repos to template:
- Follow TEMPLATE_USAGE.md exactly
- Update all placeholders
- Test locally before pushing
- Verify CI passes
- Don't skip steps

### Ecosystem Coordination Mode
When working across multiple repos:
- Start with extended-data-types
- Work in dependency order
- Test each repo independently
- Create PRs for each repo
- Don't merge until all PRs ready

## Custom Prompts

### /ecosystem-status
Check health of all ecosystem repositories:
- Clone or fetch all managed repos
- Check git status
- Review open issues/PRs
- Check CI status
- Report summary

### /update-dependencies
Update dependencies across ecosystem:
- Check for security updates
- Update pyproject.toml files
- Run tests in each repo
- Create PRs if tests pass

### /sync-template
Sync changes from template to managed repos:
- Identify changed files in template
- Apply to each managed repo
- Test each repo
- Create PRs

### /release-check
Pre-release verification:
- All tests passing
- No linting issues
- CHANGELOG.md updated
- Version will auto-increment
- Dependencies up to date

## Conversation Context

### Multi-file Context
When working on related files:
- Keep all related files in context
- Show diffs side-by-side
- Explain cross-file impacts
- Test changes together

### Long-running Tasks
For tasks requiring multiple steps:
- Break into subtasks
- Mark progress clearly
- Save state between steps
- Resume where left off
- Final verification step

## Error Handling

### CI Failures
When CI fails:
1. Read full error output
2. Identify root cause
3. Fix the issue
4. Re-run locally if possible
5. Push fix
6. Verify CI passes

### Type Check Errors
When mypy/pyright fails:
1. Read the specific error
2. Check if it's a real issue
3. Fix with proper type hints
4. Don't use `type: ignore` unless necessary
5. Document why if you must ignore

### Test Failures
When tests fail:
1. Read test output carefully
2. Identify which test failed
3. Understand what it's testing
4. Fix the code or the test
5. Run full test suite
6. Check coverage didn't drop

## Workflow Shortcuts

### Quick Fixes
For simple, obvious fixes:
- Make the change
- Run tests
- Push directly to PR branch
- No need to ask permission

### Breaking Changes
For changes that might break things:
- Explain the impact
- Show the changes
- Ask for confirmation
- Test thoroughly
- Monitor after merge

### Template Updates
When updating the template:
- Test in template repo first
- Verify all workflows pass
- Then update managed repos
- One repo at a time
- Verify each before next

## Code Style Preferences

### Python Style
- Use modern type hints (list[], dict[], not List[], Dict[])
- Prefer pathlib over os.path
- Use context managers for resources
- Keep functions focused and small
- Docstrings for public APIs

### Documentation Style
- Clear, concise language
- Examples for complex features
- Link to related docs
- Update when code changes
- Keep README up to date

### Test Style
- Descriptive test names
- One assertion per test (usually)
- Use fixtures for setup
- Test edge cases
- Mock external dependencies

## Performance Considerations

### Fast Operations
Prefer when possible:
- Parallel tool calls
- Batch operations
- Caching results
- Lazy loading
- Early returns

### Avoid
When possible avoid:
- Sequential operations that could be parallel
- Redundant file reads
- Unnecessary git operations
- Large output dumps
- Polling for status

## Communication Style

### With User
- Be concise
- Highlight important info
- Use formatting for clarity
- Show progress on long tasks
- Ask questions when unclear

### In Code Comments
- Explain why, not what
- Link to issues/PRs for context
- Update when code changes
- Remove outdated comments
- Keep them brief

### In Commit Messages
- Clear, descriptive
- Explain the change
- Reference issues if applicable
- No need for conventional commits
- But be informative

---

**Cursor Version:** Compatible with latest Cursor AI
**Last Updated:** 2025-11-25
**Maintained By:** python-library-template



<!-- Source: .ruler/ecosystem.md -->

# Unified Control Center Ecosystem

This control center manages **TWO ecosystems** from a single repository:

| Ecosystem | Path | Output |
|-----------|------|--------|
| **jbcom** | `packages/` | PyPI + npm |
| **** | `ecosystems//` | AWS/GCP infrastructure |

---

## 🏗️ ARCHITECTURE

```
jbcom-control-center/
├── packages/                          # jbcom ecosystem
│   ├── extended-data-types/           # → PyPI
│   ├── lifecyclelogging/              # → PyPI
│   ├── directed-inputs-class/         # → PyPI
│   ├── python-terraform-bridge/       # → PyPI
│   ├── vendor-connectors/             # → PyPI
│   └── agentic-control/               # → npm
│
├── ecosystems//        #  ecosystem
│   ├── terraform/
│   │   ├── modules/                   # 100+ reusable modules
│   │   └── workspaces/                # 44 live workspaces
│   ├── sam/                           # AWS Lambda apps
│   ├── lib/                           # Python libraries
│   └── config/                        # State paths, pipelines
│
└── ECOSYSTEM.toml                     # Unified manifest
```

---

## 📦 jbcom Packages

### Python (PyPI)

| Package | Description | Public Repo |
|---------|-------------|-------------|
| extended-data-types | Foundation utilities | jbcom/extended-data-types |
| lifecyclelogging | Structured logging | jbcom/lifecyclelogging |
| directed-inputs-class | Input validation | jbcom/directed-inputs-class |
| python-terraform-bridge | Terraform utils | jbcom/python-terraform-bridge |
| vendor-connectors | Cloud SDKs | jbcom/vendor-connectors |

### Node.js (npm)

| Package | Description | Public Repo |
|---------|-------------|-------------|
| agentic-control | Agent orchestration | jbcom/agentic-control |

### Dependency Chain

```
extended-data-types (foundation)
├── lifecyclelogging
├── directed-inputs-class
├── python-terraform-bridge
└── vendor-connectors (depends on all above)

agentic-control (independent Node.js package)
```

---

## 🏢  Infrastructure

### Terraform Modules (100+)

| Category | Path | Count |
|----------|------|-------|
| AWS | `terraform/modules/aws/` | 70+ |
| Google | `terraform/modules/google/` | 38 |
| GitHub | `terraform/modules/github/` | 10+ |
| Terraform | `terraform/modules/terraform/` | 5 |

### Terraform Workspaces (44)

| Organization | Path | Count |
|--------------|------|-------|
| AWS | `terraform/workspaces/terraform-aws-organization/` | 37 |
| Google | `terraform/workspaces/terraform-google-organization/` | 7 |

### SAM Applications

| App | Purpose |
|-----|---------|
| secrets-config | Secrets configuration |
| secrets-merging | Secrets merging |
| secrets-syncing | Secrets syncing |

---

## 🔑 Token Configuration

```json
{
  "tokens": {
    "organizations": {
      "jbcom": { "tokenEnvVar": "GITHUB_JBCOM_TOKEN" },
      "": { "tokenEnvVar": "GITHUB_FSC_TOKEN" }
    },
    "prReviewTokenEnvVar": "GITHUB_JBCOM_TOKEN"
  }
}
```

**Token switching is automatic** via `agentic-control`.

---

## 🔄 Release Flow

### Python Packages
```
Conventional commit → PSR version bump → PyPI publish → Public repo sync
```

### Node.js Package
```
Conventional commit → CI version bump → npm publish → Public repo sync
```

### Terraform
```
Edit → Plan → Apply (manual with appropriate credentials)
```

---

## 🔧 Working With Each Ecosystem

### jbcom Packages

```bash
# Edit
vim packages/extended-data-types/src/extended_data_types/utils.py

# Test
tox -e extended-data-types

# PR
git checkout -b fix/something
git commit -m "fix(edt): description"
git push -u origin fix/something
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create
```

###  Infrastructure

```bash
# Navigate
cd ecosystems//terraform/workspaces/terraform-aws-organization/security

# Plan
terraform plan

# Apply (requires AWS credentials)
terraform apply
```

### agentic-control

```bash
# Build
cd packages/agentic-control && pnpm build

# Test
pnpm test

# Use CLI
agentic fleet list
agentic triage analyze <session>
```

---

## ⚠️ Rules

### DO
- ✅ Use `agentic-control` for cross-ecosystem operations
- ✅ Let token switching happen automatically
- ✅ Check `ECOSYSTEM.toml` for relationships
- ✅ Use conventional commits with scopes

### DON'T
- ❌ Hardcode tokens
- ❌ Mix ecosystem concerns in single commits
- ❌ Push directly to main
- ❌ Modify Terraform state manually

---

## 📊 Health Checks

```bash
# Check Python packages
for pkg in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/$pkg --limit 1
done

# Check agentic-control
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/agentic-control --limit 1

# Check agent fleet
agentic fleet list --running
```

---

**Manifest:** `ECOSYSTEM.toml`
**Agent Config:** `agentic.config.json`
**Token Docs:** `docs/TOKEN-MANAGEMENT.md`



<!-- Source: .ruler/environment-setup.md -->

# Development Environment Setup Guide for Agents

## 🚨 CRITICAL: Tool Usage Rules

### Python Tools: Use `uvx`

**NEVER assume Python packages are available. Use `uvx` to run tools in isolated environments.**

```bash
# ❌ WRONG - Will fail with ModuleNotFoundError
python -c "import yaml; ..."

# ✅ CORRECT - Use uvx
uvx yamllint file.yml
uvx ruff check .
uvx pre-commit run --files path/to/file.yml
```

### Node.js Tools: Global Install or npx

**Ruler is a GLOBAL npm package. Run it directly as `ruler`, not via pnpm/npx.**

```bash
# ✅ CORRECT - ruler is globally installed
ruler apply

# ❌ WRONG - Don't use pnpm dlx or npx for ruler
pnpm dlx @intellectronica/ruler apply
npx @intellectronica/ruler apply

# ❌ WRONG - Don't add ruler to package.json
# It's a global tool, not a project dependency
```

### Validation: Use pre-commit

```bash
# ✅ CORRECT - Validate files with pre-commit
uvx pre-commit run --files .github/workflows/ci.yml
uvx pre-commit run yamllint --files .github/workflows/ci.yml
uvx pre-commit run --all-files
```

---

## 🤖 Anthropic Model Selection (CRITICAL)

**ALWAYS use the correct model IDs. To get the latest available models:**

```bash
curl -s "https://api.anthropic.com/v1/models" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" | jq '.data[] | {id, display_name}'
```

### Current Models (as of 2025-12)

| Model | ID | Use Case |
|-------|-----|----------|
| **Sonnet 4.5** | `claude-sonnet-4-5-20250929` | Triage, general work (DEFAULT - Haiku has schema issues) |
| **Opus 4.5** | `claude-opus-4-5-20251101` | Complex reasoning, deep analysis |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | ⚠️ Has structured output issues, avoid for triage |
| Opus 4.1 | `claude-opus-4-1-20250805` | Previous generation |
| Opus 4 | `claude-opus-4-20250514` | Previous generation |
| Sonnet 4 | `claude-sonnet-4-20250514` | Previous generation |
| Sonnet 3.7 | `claude-3-7-sonnet-20250219` | Legacy |

### Model Naming Convention

```
claude-{variant}-{major}-{minor}-{date}
         │         │       │       │
         │         │       │       └── YYYYMMDD release date
         │         │       └── Minor version (5, 1, etc.)
         │         └── Major version (4, 3, etc.)
         └── haiku, sonnet, or opus
```

**Examples:**
- ❌ `claude-4-opus` - WRONG (old naming)
- ❌ `claude-opus-4-5-20250514` - WRONG (date mismatch, Opus 4.5 is 20251101)
- ✅ `claude-sonnet-4-5-20250929` - CORRECT (Sonnet 4.5, DEFAULT)

### When to Update Models

Run the curl command above periodically to check for new models. Update:
1. `/workspace/agentic.config.json` - `defaultModel` field
2. `/workspace/packages/agentic-control/src/core/config.ts` - `DEFAULT_CONFIG.defaultModel`
3. This documentation

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



<!-- Source: .ruler/fleet-coordination.md -->

# Fleet Coordination

## agentic-control Package

The `agentic-control` package in `packages/agentic-control/` provides unified agent orchestration with automatic token switching.

### Commands

```bash
# List agents
agentic fleet list [--running]

# Spawn agent (auto-selects token based on repo org)
agentic fleet spawn <repo-url> "<task>" --ref <branch>

# Send follow-up message
agentic fleet followup <agent-id> "Message"

# Get fleet summary
agentic fleet summary

# Run bidirectional coordinator
agentic fleet coordinate --pr <number> --repo <owner/repo>

# Check token configuration
agentic tokens status
agentic tokens for-repo <owner/repo>

# AI-powered triage
agentic triage analyze <agent-id> --output report.md
agentic triage review --base main --head HEAD
```

### Configuration

All configuration is in `agentic.config.json`:

```json
{
  "tokens": {
    "organizations": {
      "jbcom": {
        "name": "jbcom",
        "tokenEnvVar": "GITHUB_JBCOM_TOKEN"
      },
      "": {
        "name": "",
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      },
      "": {
        "name": "",
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      }
    },
    "defaultTokenEnvVar": "GITHUB_TOKEN"
  },
  "defaultModel": "claude-sonnet-4-5-20250929"
}
```

## Coordination Channel (Hold-Open PR)

For multi-agent work, create a **draft PR** as communication hub:

```bash
# Create coordination branch
git checkout -b fleet/coordination-channel
echo "# Fleet Coordination" > .cursor/agents/FLEET_COORDINATION.md
git add -A && git commit -m "feat(fleet): Add coordination channel"
git push -u origin fleet/coordination-channel

# Create as DRAFT to avoid triggering AI reviewers
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --draft \
  --title "🤖 Fleet Coordination Channel (HOLD OPEN)" \
  --body "Communication channel for agent fleet. DO NOT MERGE."
```

> **Important**: Use `--draft` to prevent Amazon Q, Gemini, CodeRabbit, etc. from reviewing

## Agent Reporting Protocol

Sub-agents report status by commenting on the coordination PR:

| Format | Meaning |
|--------|---------|
| `@cursor ✅ DONE: [agent-id] [summary]` | Task completed |
| `@cursor ⚠️ BLOCKED: [agent-id] [issue]` | Needs intervention |
| `@cursor 📊 STATUS: [agent-id] [progress]` | Progress update |
| `@cursor 🔄 HANDOFF: [agent-id] [info]` | Ready for next step |

## Bidirectional Coordination Loop

The `coordinate` command runs two concurrent loops:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fleet.coordinate()                          │
│                                                                 │
│  ┌──────────────────┐              ┌────────────────────────┐  │
│  │ OUTBOUND Loop    │              │ INBOUND Loop           │  │
│  │ (every 60s)      │              │ (every 15s)            │  │
│  │                  │              │                        │  │
│  │ - Check agents   │              │ - Poll PR comments     │  │
│  │ - Send followup  │              │ - Parse @cursor        │  │
│  │ - Remove done    │              │ - Dispatch actions     │  │
│  └────────┬─────────┘              └──────────▲─────────────┘  │
│           │                                   │                │
└───────────┼───────────────────────────────────┼────────────────┘
            │                                   │
            ▼                                   │
    ┌───────────────┐                  ┌────────┴────────┐
    │ Sub-Agents    │                  │ Coordination PR │
    │ (via MCP)     │──── comment ────▶│ (GitHub inbox)  │
    └───────────────┘                  └─────────────────┘
```

## Programmatic Usage

```typescript
import { Fleet } from "agentic-control";

const fleet = new Fleet();

// Run coordination
await fleet.coordinate({
  coordinationPr: 251,
  repo: "jbcom/jbcom-control-center",
  agentIds: ["bc-xxx", "bc-yyy"],
});

// Or individual methods
await fleet.spawn({ repository: "owner/repo", task: "Do something" });
await fleet.followup("bc-xxx", "Status check");
```

## process-compose Integration

Add to `process-compose.yml`:

```yaml
fleet-coordinator:
  command: "node packages/agentic-control/dist/cli.js fleet coordinate --pr ${COORDINATION_PR} --repo jbcom/jbcom-control-center"
  environment:
    - "GITHUB_JBCOM_TOKEN=${GITHUB_JBCOM_TOKEN}"
    - "GITHUB_FSC_TOKEN=${GITHUB_FSC_TOKEN}"
    - "CURSOR_API_KEY=${CURSOR_API_KEY}"
```

Run with:
```bash
COORDINATION_PR=251 process-compose up fleet-coordinator
```



<!-- Source: .ruler/README.md -->

# Ruler Directory - AI Agent Instructions

This directory contains the **single source of truth** for all AI agent instructions across the jbcom Python library ecosystem.

## How Ruler Works

Ruler is a framework that:
1. **Centralizes** all AI agent instructions in `.ruler/*.md` files
2. **Concatenates** these files in a specific order
3. **Distributes** the combined content to agent-specific configuration files

### File Processing Order

Ruler processes files in this order:
1. `AGENTS.md` (if present) - always first
2. Remaining `.md` files in sorted order

Current files:
1. **AGENTS.md** - Core guidelines (SemVer/PSR workflow, common misconceptions)
2. **copilot.md** - Copilot-specific patterns and quick reference
3. **cursor.md** - Cursor agent modes, prompts, and workflows
4. **ecosystem.md** - Repository coordination and management

## Output Files

Ruler generates these files (DO NOT edit directly):

- **`.cursorrules`** - Cursor AI configuration
- **`.claud`** - Claude Code configuration
- **`.github/copilot-instructions.md`** - GitHub Copilot instructions
- **`AGENTS.md`** (root) - For Aider and general AI agents

All these files have a "Generated by Ruler" header and source comments.

## Making Changes

### To Update Agent Instructions

1. **Edit files in `.ruler/` directory**
   ```bash
   vim .ruler/AGENTS.md        # Core guidelines
   vim .ruler/cursor.md        # Cursor-specific
   vim .ruler/copilot.md       # Copilot patterns
   vim .ruler/ecosystem.md     # Ecosystem coordination
   ```

2. **Apply ruler to regenerate**
   ```bash
   ruler apply
   ```

3. **Review changes**
   ```bash
   git diff .cursorrules .github/copilot-instructions.md AGENTS.md
   ```

4. **Commit everything**
   ```bash
   git add .ruler/ .cursorrules .github/copilot-instructions.md AGENTS.md
   git commit -m "Update agent instructions via ruler"
   ```

### Configuration

Edit `.ruler/ruler.toml` to configure:
- Which agents are active by default
- Custom output paths for specific agents
- Nested rule loading (for subdirectory-specific rules)

Current configuration:
```toml
default_agents = ["copilot", "cursor", "claude", "aider"]

[agents.copilot]
enabled = true
output_path = ".github/copilot-instructions.md"

[agents.cursor]
enabled = true
# Uses default .cursorrules

[agents.claude]
enabled = true
# Uses default .claud

[agents.aider]
enabled = true
output_path_instructions = "AGENTS.md"
```

## File Purposes

### AGENTS.md
**Primary audience:** All AI agents
**Content:**
- python-semantic-release (PSR) workflow and rationale
- Why manual versioning is prohibited
- PR and release workflows
- Common agent misconceptions
- Development workflows
- Template maintenance guidelines

**Key sections:**
- CI/CD Design Philosophy
- Version Management
- Agent Approval Instructions
- Common Misconceptions

### copilot.md
**Primary audience:** GitHub Copilot
**Content:**
- Quick reference rules
- Code patterns and examples
- Testing patterns
- Common tasks (adding functions, fixing bugs, refactoring)
- Error message guidelines
- Security best practices

**Format:** Short, actionable examples with ✅/❌ comparisons

### cursor.md
**Primary audience:** Cursor AI
**Content:**
- Background agent modes (review, maintenance, migration, ecosystem)
- Custom prompts (`/ecosystem-status`, `/update-dependencies`, etc.)
- Error handling workflows
- Code style preferences
- Performance considerations
- Communication guidelines

**Format:** Operational guidelines for different work modes

### ecosystem.md
**Primary audience:** All agents doing cross-repo work
**Content:**
- Managed repository documentation
- Dependency graph
- Coordination guidelines
- Release coordination process
- Maintenance schedules
- Agent instructions for ecosystem work

**Format:** Reference documentation with procedures

## Best Practices

### Writing Agent Instructions

1. **Be explicit** - Don't assume agents understand context
2. **Use examples** - Show both good (✅) and bad (❌) patterns
3. **Explain why** - Not just what to do, but why it matters
4. **Anticipate mistakes** - Document common misconceptions
5. **Keep updated** - Revise based on agent behavior

### Organizing Content

- **General guidelines** → `AGENTS.md`
- **Agent-specific patterns** → `{agent}.md`
- **Domain-specific** → Separate files (e.g., `ecosystem.md`)
- **Quick reference** → Use bullet points and code examples
- **Deep explanations** → Use sections with rationale

### Testing Changes

After updating ruler content:

1. **Apply ruler**
   ```bash
   ruler apply
   ```

2. **Test with actual agents**
   - Ask Cursor to perform a task
   - Check if Copilot suggestions align
   - Verify agents follow new guidelines

3. **Iterate based on behavior**
   - If agents still make mistakes, clarify instructions
   - Add more examples if needed
   - Update misconceptions section

## Advanced Usage

### Dry Run

Preview what ruler will do:
```bash
ruler apply --dry-run
```

### Specific Agents

Apply only for certain agents:
```bash
ruler apply --agents copilot,cursor
```

### Verify Generated Files

After applying ruler, check that generated files:
1. Have "Generated by Ruler" header
2. Include all source files
3. Maintain proper formatting
4. Match expected structure

## Maintenance

### When to Update

Update ruler content when:
- Agents consistently misunderstand something
- New workflows or patterns emerge
- Ecosystem grows (new repos)
- Template changes significantly
- Agent tools/capabilities change

### Version History

Track changes to ruler content in git:
- Commit messages should explain what behavior changed
- Tag major instruction updates
- Document breaking changes for agents

### Testing Framework

Consider adding:
- Example prompts that test agent understanding
- Expected vs actual behavior documentation
- Agent response validation

## Integration with Template

This ruler setup is part of the python-library-template:

- **Template repos** - Use this exact structure
- **Managed repos** - Receive updates from template
- **Synchronization** - Ruler changes propagate via template updates

## Resources

- **Ruler Documentation:** https://github.com/intellectronica/ruler
- **Template Usage:** /workspace/TEMPLATE_USAGE.md
- **Ecosystem Guide:** /workspace/ECOSYSTEM.md

---

**Ruler Version:** Compatible with @intellectronica/ruler latest
**Last Updated:** 2025-11-25
**Maintained By:** python-library-template
