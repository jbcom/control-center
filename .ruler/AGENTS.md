# AI Agent Guidelines for jbcom-control-center

**This is the monorepo for jbcom Python ecosystem packages.** All packages are managed here with unified CI/CD.

## 🚨 MANDATORY FIRST: SESSION START

### Session Start Checklist:
```bash
# 1. Read core agent rules
cat .ruler/AGENTS.md
cat .ruler/fleet-coordination.md

# 2. Check active GitHub Issues for context
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list --label "agent-session" --state open

# 3. Check your fleet tooling
node packages/cursor-fleet/dist/cli.js list --running
```

### Your Tools:
| Tool | Command | Purpose |
|------|---------|---------|
| Fleet management | `cursor-fleet list/spawn/followup` | Manage Cursor background agents |
| Fleet coordination | `cursor-fleet coordinate --pr N` | Bidirectional agent coordination |
| Sub-agent spawn | `cursor-fleet spawn <repo> <task>` | Spawn agents in repos |

## 🔑 CRITICAL: Authentication

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
```

## 📦 Monorepo Structure

```
packages/
├── extended-data-types/      # Foundational utilities
├── lifecyclelogging/         # Structured logging
├── directed-inputs-class/    # Input handling (decorators + legacy)
├── python-terraform-bridge/  # Terraform integration
├── vendor-connectors/        # Cloud vendor connectors (AWS, Google, GitHub)
└── cursor-fleet/             # TypeScript - Agent fleet management
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
- [ ] ALL medium severity items resolved or justified with technical reasoning
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
# Install with uv
uv sync

# Run tests for a package
cd packages/directed-inputs-class
uv run pytest tests/ -v

# Run lint
uv run ruff check packages/
uv run ruff format --check packages/
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
# Spawn agent in another repo
node packages/cursor-fleet/dist/cli.js spawn \
  "https://github.com/jbcom/vendor-connectors" \
  "Fix CI failures" \
  --ref main

# Send followup to running agent
node packages/cursor-fleet/dist/cli.js followup <agent-id> "Update: ..."

# Monitor agents
node packages/cursor-fleet/dist/cli.js list --running
```

### Bidirectional Coordination
```bash
# Start coordinator (uses PR for communication)
node packages/cursor-fleet/dist/cli.js coordinate --pr 251 --repo jbcom/jbcom-control-center
```

---

**Last Updated:** 2025-11-30
**Versioning:** SemVer via python-semantic-release (per-package)
**Status:** Production monorepo for jbcom ecosystem
