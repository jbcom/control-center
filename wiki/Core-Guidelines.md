# AI Agent Guidelines for Python Library Template (jbcom ecosystem)

**This is the DEFINITIVE Python library template** for the jbcom ecosystem. All configuration, workflows, and agent instructions here represent the consolidated best practices from multiple production deployments.

## 🚨 MANDATORY FIRST: KNOW YOUR OWN TOOLING

**YOU HAVE COMPREHENSIVE TOOLING. READ IT. USE IT. NEVER ASK THE USER ABOUT IT.**

### Session Start Checklist (DO THIS FIRST):
```bash
# 1. Memory Bank State
cat memory-bank/activeContext.md
cat memory-bank/progress.md
cat memory-bank/agenticRules.md

# 2. YOUR Tooling Documentation
cat docs/CURSOR-AGENT-MANAGEMENT.md   # How to spawn sub-agents
cat docs/AGENTIC-DIFF-RECOVERY.md     # Forensic recovery with aider
cat docs/AGENT-TO-AGENT-HANDOFF.md    # Station-to-station handoffs

# 3. YOUR Scripts
ls -la .cursor/scripts/               # Available tooling scripts
```

### Your Tools (USE THEM):
| Tool | Command | Purpose |
|------|---------|---------|
| Sub-agent management | `cursor-agents list/create/status` | Spawn opus 4.5 agents for parallel work |
| Offline triage | `agent-triage-local analyze/decompose` | Process conversations without MCP |
| Swarm orchestrator | `agent-swarm-orchestrator` | Spawn multiple recovery agents |
| Batch pipeline | `triage-pipeline` | Automated session recovery |
| AI forensics | `aider --message "..."` | Code analysis and recovery |
| Memory replay | `python scripts/replay_agent_session.py` | Update memory bank |

### Spawn Sub-Agents (DO THIS FOR PARALLEL WORK):
```bash
# Spawn background agents for tasks
cursor-agents create "🤖 Review and merge PR #203 in terraform-modules"
cursor-agents create "🤖 Fix CI failures in vendor-connectors repo"

# Or create GitHub issues for async agent pickup
gh issue create --repo FlipsideCrypto/terraform-modules \
  --title "🤖 Agent Task: Merge PR #203" \
  --body "Background agent task..."
```

**IF YOU ASK THE USER ABOUT YOUR OWN TOOLING, YOU HAVE FAILED.**

---

## 🎯 CRITICAL: PR Ownership Rule (READ WHEN WORKING WITH PRs!)

**If you are working on a Pull Request, this rule applies.**

**For Cursor background agents:** See `.cursor/rules/05-pr-ownership.mdc` for complete protocol.
**For other agents:** See summary below.

Key points:
- **First agent on PR = PR Owner** - You own ALL feedback, issues, and collaboration
- **Engage with AI agents directly** - Respond to @gemini-code-assist, @copilot, etc.
- **Free the user** - Handle everything that doesn't need human judgment
- **Collaborate, don't escalate** - Resolve AI-to-AI conflicts yourself
- **Merge when ready** - Execute merge after all feedback addressed

**🔬 VERIFICATION REQUIREMENT (NEW):**
- **All version claims MUST be verified** against official sources (https://go.dev/dl/, https://releases.rs/, etc.)
- **Never rely on training data** for version numbers or tool specifications
- **Official installation methods** (like rustup.rs curl-to-shell) are NOT security vulnerabilities
- **Document your verification** sources in responses

See `.cursor/rules/15-pr-review-verification.mdc` (Cursor) or full details below (other agents).
See `.cursor/rules/REFERENCE-pr-ownership-details.md` for detailed examples and templates.

## 🔑 CRITICAL: Authentication (READ FIRST!)

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh workflow run "Release" --repo jbcom/jbcom-control-center
```

### Token Reference:
- **GITHUB_JBCOM_TOKEN** - Use for ALL jbcom repo operations (PRs, merges, workflow triggers)
- **CI_GITHUB_TOKEN** - Used by GitHub Actions workflows (in repo secrets)
- **PYPI_TOKEN** - Used by release workflow for PyPI publishing (in repo secrets)

### ⚠️ NEVER FORGET:
The default `GH_TOKEN` does NOT have access to jbcom repos. You MUST prefix with `GH_TOKEN="$GITHUB_JBCOM_TOKEN"` for EVERY `gh` command targeting jbcom repos.

## 🎯 PURPOSE: Agentic Template Repository

This template is designed for:
1. **Human developers** starting new Python libraries
2. **AI coding assistants** (Cursor, Codex, Copilot, Gemini) helping maintain the ecosystem
3. **Background agents** performing automated maintenance tasks

### Template Usage

When creating a new library from this template:
1. Update `pyproject.toml` with your project name and details
2. Replace `${REPO_NAME}` in documentation with your actual repo name
3. Add PSR config to `pyproject.toml` (see `packages/*/pyproject.toml` for examples)
4. Copy `.github/workflows/ci.yml` and update PyPI project name
5. Run `ruler apply` to regenerate agent-specific instructions

## 🚨 CRITICAL: CI/CD Workflow Design Philosophy

### Automated Release Workflow with python-semantic-release

**This repository uses python-semantic-release (PSR) for per-package versioning with Git tag tracking**. Releases are triggered automatically based on conventional commits when merging to main.

This approach was adopted to fix:
- Version commit-back issues (versions weren't being tracked in git)
- PyPI "file already exists" errors from duplicate version numbers
- Shared versioning across packages (each package now has independent versions)

### Key Design Decisions

#### 1. **CalVer-Compatible Semantic Versioning**

✅ **How It Works:**
- Version format: `YYYYMM.MINOR.PATCH`
- Example: `202511.3.0`
- Major version (`202511`) maintains CalVer backward compatibility
- Minor/patch follow SemVer semantics based on conventional commits
- Each package is versioned independently via Git tags
- Config: `packages/*/pyproject.toml` under `[tool.semantic_release]`

✅ **CORRECT Understanding:**
- Version bumps based on conventional commit types
- Git tags track state per package (e.g., `extended-data-types-v202511.3.0`)
- Changelog generated automatically from commits
- Versions committed back to repo

#### 2. **Conventional Commits Drive Releases**

✅ **How It Works:**
```
Merge PR to main branch
  ↓
PSR analyzes conventional commits
  ↓
Determine version bump per package (based on file changes + scopes)
  ↓
Create Git tags and commit version updates
  ↓
Build signed package
  ↓
Publish to PyPI
  ↓
DONE
```

**Package Scopes:**
| Scope | Package | Tag Format |
|-------|---------|------------|
| `edt` | extended-data-types | `extended-data-types-v{version}` |
| `logging` | lifecyclelogging | `lifecyclelogging-v{version}` |
| `dic` | directed-inputs-class | `directed-inputs-class-v{version}` |
| `connectors` | vendor-connectors | `vendor-connectors-v{version}` |

**Commit Type to Bump:**
| Type | Bump | Example |
|------|------|---------|
| `feat` | Minor | `feat(edt): add utility` → `202511.3.0` → `202511.4.0` |
| `fix`, `perf` | Patch | `fix(logging): handle error` → `202511.3.0` → `202511.3.1` |
| `feat!` or `BREAKING CHANGE:` | Major | → `202512.0.0` |
| `docs`, `chore`, etc. | None | No release |

#### 3. **Git Tags Track Release State**

✅ **What We Do:**
- Create per-package Git tags (e.g., `extended-data-types-v202511.3.0`)
- Commit version updates back to repo
- Auto-generate CHANGELOG per package
- Publish to PyPI with proper attestations

✅ **Benefits:**
- Independent per-package versioning
- No more duplicate version errors on PyPI
- Clear release history via Git tags
- Changelog generation from commits

#### 4. **Why This Approach?**

**Problems This Solves:**
- ✅ Version state tracking (Git tags per package)
- ✅ Version commit-back (PSR handles this)
- ✅ Per-package releases (independent versioning)
- ✅ Changelog generation (automatic from commits)
- ✅ No more PyPI "file already exists" errors

**Trade-offs:**
- Requires conventional commit format
- More configuration per package
- Depends on Git tag history

## 📝 Making Code Changes

### When Reviewing PRs

**DO:**
- ✅ Review code quality and correctness
- ✅ Check test coverage
- ✅ Verify type hints
- ✅ Suggest API improvements
- ✅ Check for security issues
- ✅ Verify dependencies are up to date
- ✅ Ensure commit messages follow conventional format

**DO NOT:**
- ❌ Recommend manual version management
- ❌ Flag python-semantic-release as "wrong" approach
- ❌ Suggest removing Git tags (they track release state)
- ❌ Manually edit `__version__` in packages

### Understanding Version Management

```
Merge PR to main
  ↓
PSR analyzes commits with monorepo parser
  ↓
Filters commits by package path + scope
  ↓
Determines bump: feat→minor, fix→patch, feat!→major
  ↓
Updates pyproject.toml + __init__.py
  ↓
Creates Git tag (e.g., extended-data-types-v202511.4.0)
  ↓
Commits changes back to main
  ↓
Builds and publishes to PyPI
```

**Version is:**
- ✅ Generated based on conventional commit analysis
- ✅ Tracked per package via Git tags
- ✅ Written to `pyproject.toml` and `__init__.py`
- ✅ Committed back to repository
- ✅ Independent per package

### The Monorepo Parser

Key features of `scripts/psr/monorepo_parser.py`:
- **Filters commits** by package directory (`path_filters`)
- **Supports scopes** for targeting packages (`scope_prefix`)
- **Handles** conventional commit types (feat, fix, perf, etc.)
- **Detects breaking changes** via `!` suffix or `BREAKING CHANGE:` footer

### Commit Message Format (REQUIRED)

Conventional commits are **required** for proper versioning:

```bash
# Format
<type>(<scope>): <description>

# Examples
feat(edt): add new serialization utility        # Minor bump
fix(logging): handle edge case in formatter    # Patch bump
feat(connectors)!: redesign API                # Major bump

# Scope mappings
edt        → extended-data-types
logging    → lifecyclelogging
dic        → directed-inputs-class
connectors → vendor-connectors
```

## 🤖 For AI Agents: Approval & Override Instructions

### Background Agent Behavior

When you are operating as a **background agent** (autonomous, no user interaction):

**CRITICAL RULES:**
1. **DO NOT** create or merge PRs without explicit user approval
2. **DO NOT** push directly to main branch
3. **DO** create PRs and mark them as ready for review
4. **DO** run all CI checks and fix linting/test failures
5. **DO** respond to PR feedback and iterate
6. **WAIT** for human approval before merging

**EXCEPTION - When User Says:**
> "merge it", "go ahead and merge", "merge to main", "just push it"

Then you MAY:
- Merge PRs after CI passes
- Push directly to main if explicitly instructed
- Skip the usual "wait for approval" step

**HOW TO MERGE:**
```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

### Interactive Agent Behavior

When you are in **interactive mode** (user is actively engaged):

**DEFAULT BEHAVIOR:**
- Ask for confirmation before major actions
- Present options and let user decide
- Show diffs and explain changes

**WHEN USER GETS FRUSTRATED:**
User signals like "just do it", "stop asking", "I don't care", "fucking do it":
- Switch to autonomous mode
- Make decisions based on best practices in this document
- Execute without asking for every little thing
- Still verify after major milestones

### PR Review Response

When PR feedback arrives (from Copilot, Gemini, human reviewers):

1. **READ the feedback carefully**
2. **CHECK** if feedback contradicts this document
3. **IF** feedback suggests semantic-release, git tags, or manual versioning:
   - Politely explain our CalVer approach
   - Reference this document
   - Do NOT implement the suggestion
4. **IF** feedback is about code quality, bugs, or improvements:
   - Implement the feedback
   - Push fixes
   - Verify CI passes

### Template Maintenance Tasks

As an agent maintaining this template:

**ALLOWED:**
- Update dependencies
- Fix security vulnerabilities
- Improve documentation clarity
- Add helpful examples
- Fix bugs in scripts or workflows

**NOT ALLOWED WITHOUT USER APPROVAL:**
- Change the versioning approach
- Modify CI workflow structure
- Remove or bypass safety checks
- Change the release process

## 🔧 Development Workflow

### Local Development

```bash
# Install dependencies
pip install -e ".[tests,typing,docs]"  # or use poetry/uv

# Run tests
pytest

# Run type checking
mypy src/  # or pyright

# Run linting
pre-commit run --all-files
```

### Creating PRs

1. Create a feature branch
2. Make your changes
3. Run tests locally
4. Create PR against `main`
5. CI will run automatically
6. Address any feedback
7. Merge to main when approved

### Releases (Fully Automated)

When PR is merged to main:
1. CI runs all checks
2. PSR analyzes conventional commits per package
3. Determines version bump (feat→minor, fix→patch, feat!→major)
4. Creates Git tag and commits version update
5. Builds signed package with attestations
6. Publishes to PyPI
7. **DONE**

Releases are driven by conventional commits - use proper types and scopes.

## 🎯 Common Agent Misconceptions

### Misconception #1: "Missing version management"
**Agent says:** "You need to manually update __version__ before releases"
**Reality:** python-semantic-release handles versioning automatically based on conventional commits. Never manually edit `__version__`.

### Misconception #2: "Conventional commits are optional"
**Agent says:** "Any commit format works"
**Reality:** Conventional commits are **required** for PSR to determine version bumps. Use proper types (`feat`, `fix`, `perf`) and scopes (`edt`, `logging`, `dic`, `connectors`).

### Misconception #3: "Git tags are unnecessary"
**Agent says:** "Remove git tags, they're clutter"
**Reality:** Git tags are **required** for PSR to track release state per package. Each package has its own tag format (e.g., `extended-data-types-v202511.3.0`).

### Misconception #4: "Should use pure CalVer"
**Agent says:** "Use simple YYYY.MM.BUILD without semantic versioning"
**Reality:** We use CalVer-compatible semantic versioning (`YYYYMM.MINOR.PATCH`). This gives us CalVer's date-based major versions plus SemVer's minor/patch semantics.

### Misconception #5: "All packages should share versions"
**Agent says:** "Sync versions across all packages"
**Reality:** Each package is versioned independently. This allows releasing only packages that changed, not the entire monorepo.

### Misconception #6: "Scopes are optional"
**Agent says:** "Just use `feat: description` without scope"
**Reality:** Scopes are used by the monorepo parser to target specific packages. While unscoped commits can work if files match path filters, using scopes is preferred.

### Misconception #7: "CHANGELOG is manual"
**Agent says:** "You need to manually maintain CHANGELOG.md"
**Reality:** python-semantic-release auto-generates changelogs from conventional commits. Focus on writing good commit messages instead.

## 📚 Design Rationale

This workflow was created to solve REAL problems we encountered with the previous pycalver approach:

**Problems We Solved:**
- ✅ No more PyPI "file already exists" errors (versions now tracked via Git tags)
- ✅ No more version conflicts between packages (independent per-package versioning)
- ✅ No more missing version commit-back (PSR commits versions to repo)
- ✅ Clear release history via Git tags per package
- ✅ Automatic changelog generation from commits

**Benefits We Gained:**
- ✅ Predictable: conventional commits → deterministic version bumps
- ✅ Independent: each package versioned separately
- ✅ Traceable: Git tags show exact release state
- ✅ Documented: auto-generated changelogs
- ✅ Monorepo-aware: custom parser filters by path + scope

**Trade-offs Accepted:**
- Requires conventional commit discipline
- More per-package configuration
- Depends on Git tag history for state

## 🧪 Testing the Workflow

### Local Testing

Test PSR locally (dry run):
```bash
cd packages/extended-data-types
semantic-release version --print --no-commit --no-tag

# Check what version would be next
semantic-release version --print-last-released
```

### CI Testing

Test in a PR:
1. Create a PR with conventional commits
2. Watch CI run
3. Verify all checks pass
4. Check that PSR can determine version bump from commits

### Release Testing

To test an actual release:
1. Merge a PR to main with `feat(edt): ...` or `fix(edt): ...`
2. Watch the CI release job run
3. Verify Git tag was created (e.g., `extended-data-types-v202511.4.0`)
4. Verify version was committed back to repo
5. Verify publish to PyPI succeeded
6. Install from PyPI and verify: `pip install extended-data-types==202511.4.0`

## 🤝 Getting Help

### For AI Agents

If you're an AI agent uncertain about a suggestion:
1. **Check this document first** - it's comprehensive
2. If it involves versioning or releases, understand PSR workflow before suggesting changes
3. Focus on code quality, tests, and proper conventional commits
4. Trust that per-package versioning via Git tags is intentional
5. When in doubt, ask the user instead of assuming

### For Human Developers

- Use conventional commits consistently for proper versioning
- Don't manually edit `__version__` - PSR handles it
- If something seems weird, check this document first
- Each package versions independently via Git tags
- Trust the process - it works

---

**Last Updated:** 2025-11-28
**Versioning:** CalVer-compatible SemVer (YYYYMM.MINOR.PATCH) via python-semantic-release
**Status:** Production-tested across jbcom ecosystem
**Release Tracking:** Git tags per package
