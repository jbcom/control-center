# AI Agent Guidelines for jbcom Control Center

**This is the control center** for the jbcom Python library ecosystem. It manages multiple packages via a monorepo architecture.

## 🚨 MANDATORY FIRST: SESSION START

### Session Start Checklist (DO THIS FIRST):
```bash
# 1. Read core agent rules
cat .ruler/AGENTS.md
cat .ruler/fleet-coordination.md

# 2. Check active GitHub Issues for context
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list --label "agent-session" --state open

# 3. Check your fleet tooling
cd /workspace/packages/cursor-fleet && node dist/cli.js list 2>/dev/null || echo "Fleet not built"
```

### Your Tools:
| Tool | Command | Purpose |
|------|---------|---------|
| Fleet management | `node packages/cursor-fleet/dist/cli.js list` | List Cursor background agents |
| Fleet replay | `node packages/cursor-fleet/dist/cli.js replay <agent-id> -o <dir>` | Recover agent conversation |
| Fleet spawn | `node packages/cursor-fleet/dist/cli.js spawn --repo R --task T` | Spawn agents in repos |

### Session Tracking (USE GITHUB ISSUES):
```bash
# Create session context issue
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create \
  --label "agent-session" \
  --title "🤖 Agent Session: $(date +%Y-%m-%d)" \
  --body "## Context

## Progress

## Blockers"

# Update session progress
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue comment <NUMBER> --body "## Update: ..."

# Close when done
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue close <NUMBER>
```

---

## 🔑 CRITICAL: Authentication (READ FIRST!)

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
```

### Token Reference:
- **GITHUB_JBCOM_TOKEN** - Use for ALL jbcom repo operations (PRs, merges, workflow triggers)
- **CI_GITHUB_TOKEN** - Used by GitHub Actions workflows (in repo secrets)
- **PYPI_TOKEN** - Used by release workflow for PyPI publishing (in repo secrets)

### ⚠️ NEVER FORGET:
The default `GH_TOKEN` does NOT have access to jbcom repos. You MUST prefix with `GH_TOKEN="$GITHUB_JBCOM_TOKEN"` for EVERY `gh` command targeting jbcom repos.

---

## 🚨 CRITICAL: CI/CD Workflow - THE ACTUAL SYSTEM

### Python Semantic Release (PSR)

**This repository uses Python Semantic Release** for versioning and publishing.

### How It ACTUALLY Works:

```
Push to main branch
  ↓
CI runs all tests
  ↓
semantic-release analyzes commits (conventional commits)
  ↓
IF version bump needed:
  ├── Updates version in pyproject.toml
  ├── Creates git tag (e.g., extended-data-types-v202511.6.0)
  ├── Pushes tag and version commit
  └── Publishes to PyPI
  ↓
IF no version bump needed:
  └── Skips release (no changes detected)
```

### Version Format

**Format**: `YYYYMM.MINOR.PATCH` (e.g., `202511.7.0`)
- Uses CalVer-style YYYYMM prefix
- Minor/patch bumped by conventional commits
- NOT simple auto-increment - uses commit analysis

### Conventional Commits ARE REQUIRED

The release system REQUIRES conventional commit messages:

| Prefix | Effect | Example |
|--------|--------|---------|
| `feat:` | Minor bump | `feat(dic): add decorator API` |
| `fix:` | Patch bump | `fix(vc): resolve import error` |
| `feat!:` or `BREAKING CHANGE:` | Major bump | `feat!: remove deprecated API` |
| `chore:`, `docs:`, `ci:` | No release | `docs: update README` |

### Git Tags ARE USED

**Per-package tags exist:**
```
extended-data-types-v202511.6.0
lifecyclelogging-v202511.6.0
directed-inputs-class-v202511.7.0
vendor-connectors-v202511.10.0
```

### Package Release Order

Packages are released sequentially in dependency order:
1. `extended-data-types` (foundation - no deps)
2. `lifecyclelogging` (depends on EDT)
3. `directed-inputs-class` (depends on EDT)
4. `vendor-connectors` (depends on all above)

---

## 📦 Monorepo Structure

```
jbcom-control-center/
├── packages/
│   ├── extended-data-types/    → jbcom/extended-data-types → PyPI
│   ├── lifecyclelogging/       → jbcom/lifecyclelogging → PyPI
│   ├── directed-inputs-class/  → jbcom/directed-inputs-class → PyPI
│   ├── vendor-connectors/      → jbcom/vendor-connectors → PyPI
│   ├── python-terraform-bridge/ → (internal, released to PyPI)
│   └── cursor-fleet/           → (internal tooling, Node.js)
├── .ruler/                     → Agent rules (SOURCE OF TRUTH)
├── .cursor/rules/              → Cursor-specific rules
└── .github/workflows/          → CI/CD pipelines
```

### Edit Code Here

All package code is in `packages/`. Edit directly:
```bash
vim packages/extended-data-types/src/extended_data_types/type_utils.py
vim packages/vendor-connectors/pyproject.toml
```

### Run Tests

```bash
# Using tox (as CI does)
tox -e extended-data-types
tox -e vendor-connectors

# Or directly
cd packages/vendor-connectors && uv run pytest
```

---

## 🎯 PR Ownership Rule

**If you are working on a Pull Request:**

- **First agent on PR = PR Owner** - You own ALL feedback, issues, and collaboration
- **Engage with AI agents directly** - Respond to @gemini-code-assist, @copilot, etc.
- **Free the user** - Handle everything that doesn't need human judgment
- **Merge when ready** - Execute merge after all feedback addressed

See `.cursor/rules/05-pr-ownership.mdc` for complete protocol.

---

## 🤖 For AI Agents: Behavior Guidelines

### Background Agent Behavior

When operating as a **background agent**:

1. **DO NOT** push directly to main branch
2. **DO** create PRs and mark them as ready for review
3. **DO** run all CI checks and fix linting/test failures
4. **DO** respond to PR feedback and iterate
5. **WAIT** for human approval before merging

**EXCEPTION - When User Says:**
> "merge it", "go ahead and merge", "merge to main"

Then you MAY merge PRs after CI passes.

**HOW TO MERGE:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <PR_NUMBER> --squash --delete-branch
```

### Commit Message Rules

Since releases depend on conventional commits:

```bash
# Feature (minor bump)
git commit -m "feat(dic): add new decorator API"

# Fix (patch bump)
git commit -m "fix(vc): resolve authentication bug"

# No release trigger
git commit -m "docs: update README"
git commit -m "chore: update dependencies"

# Use scope for package clarity
# dic = directed-inputs-class
# vc = vendor-connectors
# edt = extended-data-types
# ll = lifecyclelogging
# ptb = python-terraform-bridge
```

---

## 🔧 Development Workflow

### Local Development

```bash
# Install all packages in dev mode
uv sync --extra dev

# Run tests for specific package
tox -e vendor-connectors

# Run linting
uvx ruff check packages/
uvx ruff format --check packages/
```

### Creating PRs

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make changes with proper conventional commits
3. Run tests locally: `tox -e <package>`
4. Create PR: `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create`
5. Wait for CI and address feedback
6. Merge when approved

### Releases

**Releases are automatic on merge to main:**
1. CI runs all checks
2. semantic-release analyzes commits
3. If `feat:` or `fix:` commits found → release triggered
4. Package published to PyPI
5. Public repo synced

**Check release status:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/jbcom-control-center --limit 5
```

---

## 📋 Quick Reference

### Common Commands

```bash
# List PRs
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr list

# Check CI status
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --limit 5

# Merge PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch

# Check PyPI versions
pip index versions extended-data-types
pip index versions vendor-connectors

# Run tests
tox -e extended-data-types
tox -e vendor-connectors
```

### Package Scopes for Commits

| Package | Scope |
|---------|-------|
| extended-data-types | `edt` |
| lifecyclelogging | `ll` |
| directed-inputs-class | `dic` |
| vendor-connectors | `vc` |
| python-terraform-bridge | `ptb` |
| cursor-fleet | `fleet` |

---

**Last Updated:** 2025-11-30
**Versioning:** Python Semantic Release with CalVer-style format
**Status:** Production - packages released to PyPI
