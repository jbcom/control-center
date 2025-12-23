# Copilot Instructions - jbcom Control Center

This repo is a **centralized hub** for managing 20+ GitHub repositories across multiple ecosystems (Python, Node.js, Go, Terraform). Before any task, understand the two core workflows below.

## Architecture: Repository Management Hub

**Three interconnected systems:**

1. **Configuration Layer** (`repo-config.json`, `agentic.config.json`)
   - Single source of truth for all managed repo settings
   - Defines merge rules, security policies, branch protection, labels
   - Maps repository names to projects and dependencies

2. **File Sync System** (`repository-files/`, `.github/workflows/ecosystem-sync.yml`)
   - Syncs Cursor rules, GitHub workflows, and CI configs to 20+ repos
   - Three tiers: `always-sync/` (overwrites), `initial-only/` (first PR only), language-specific (`python/`, `nodejs/`, `go/`, `terraform/`)
   - Triggered by `ecosystem-sync.yml` workflow → creates PRs to repos

3. **CLI Tools** (`scripts/ecosystem`, `scripts/configure-repos`, `scripts/sync-files`)
   - Local preview/validation before sync
   - Direct repo configuration via `gh` CLI

## Before Starting: The Session Protocol

**Always start with:**
```bash
cat memory-bank/activeContext.md      # Current focus
cat memory-bank/progress.md           # Recent work
```

**Always end with:**
```bash
cat >> memory-bank/activeContext.md << EOF

## Session: $(date +%Y-%m-%d)

### Completed
- [x] Your work here

### For Next Agent
- [ ] Follow-up tasks
EOF
```

## Critical Workflows & Commands

### 1. Syncing Files to Managed Repos
```bash
# Preview changes (DRY RUN)
./scripts/sync-files --dry-run --all

# Apply changes to all repos
./scripts/sync-files --all

# Sync to specific repo
./scripts/sync-files --repo jbcom/python-agentic-crew
```

**Example:** Adding a new Cursor rule
- Add file to `repository-files/always-sync/.cursor/rules/new-rule.mdc`
- Run sync command above
- Inspect the generated PRs

### 2. Configuring Repository Settings
```bash
# Preview repo configuration changes
./scripts/configure-repos --dry-run --all

# Apply settings from repo-config.json
./scripts/configure-repos --all

# Configure single repo
./scripts/configure-repos --repo jbcom/nodejs-agentic-control
```

### 3. Managing Repository Ecosystem
```bash
# Discover all repos in org
./scripts/ecosystem discover

# Check ecosystem health (CI status, dependencies)
./scripts/ecosystem health

# Show dependency graph
./scripts/ecosystem deps

# Generate CI matrix for workflows
./scripts/ecosystem matrix
```

### 4. Testing Locally Before Sync
```bash
# Validate all shell scripts
bash -n scripts/ecosystem scripts/configure-repos scripts/sync-files

# Validate JSON configs
jq empty repo-config.json agentic.config.json

# Check workflow files
./scripts/check-workflow-consistency
```

## Project Structure Guide

**Key directories to understand:**

- `repository-files/` — Files synced to managed repos
  - `always-sync/` — Overwrites every time (Cursor rules, workflows)
  - `initial-only/` — Only sync on first PR (licenses, base configs)
  - `python/`, `nodejs/`, `go/`, `terraform/` — Language-specific rules
- `scripts/` — Bash CLI tools for repo management
- `docs/` — Architecture and runbook docs
- `memory-bank/` — Session context for AI agents
- `.cursor/rules/` — Cursor IDE rules (don't edit—synced via `repository-files/`)

## Patterns & Conventions

### Commit Message Format
```
<type>(<scope>): <description>

<optional body explaining the why>
```

Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `ci`, `test`

Examples:
```bash
feat(sync): add Cursor rule for Python documentation
fix(config): correct merge settings for nodejs repos
ci(ecosystem): add matrix generation for 25 repos
docs: update token management procedures
```

### Common Tasks

**Adding a new managed repository:**
1. Add repo to `agentic.config.json` → `ecosystem.managedRepos[]`
2. Add dependency info to `agentic.config.json` → `ecosystem.dependencyGraph`
3. Update `repo-config.json` if custom settings needed
4. Run `./scripts/ecosystem discover` to verify

**Updating a Cursor rule across all repos:**
1. Edit `repository-files/always-sync/.cursor/rules/*.mdc`
2. Run `./scripts/sync-files --dry-run --all` to preview
3. Review generated PR changes
4. Run `./scripts/sync-files --all` to apply

**Fixing repository settings:**
1. Edit `repo-config.json` with new settings
2. Run `./scripts/configure-repos --dry-run --repo <name>` to preview
3. Run `./scripts/configure-repos --repo <name>` to apply

### Critical Details

- **No symlinks** — See `../docs/NO-SYMLINKS-POLICY.md`
- **Merge strategy** — Squash-only merges (no merge commits)
- **Authentication** — Single `GITHUB_TOKEN` for all operations (same token in CI)
- **Branches** — Main branch is `main` across all repos
- **Archived repos** — Removed from sync targets; kept private in `jbcom/` org

## When Things Break

**Workflow failures?** Check:
- `agentic.config.json` → is the repo still in `managedRepos[]`?
- `repo-config.json` → do settings need updating for that repo?
- `memory-bank/activeContext.md` → recent changes that might affect it?

**Sync creating wrong PRs?** Run:
```bash
./scripts/sync-files --dry-run --all | grep "your-repo" -A5
```

**Tests failing?** Most tasks don't have tests. Check for errors in:
- Shell syntax: `bash -n scripts/*`
- JSON validity: `jq empty *.json`
- Workflow consistency: `./scripts/check-workflow-consistency`

## Resources

- `../docs/TOKEN-MANAGEMENT.md` — How GitHub tokens work
- `../docs/TRIAGE-HUB.md` — Triage workflow and issue tracking
- `../docs/MIGRATION.md` — jbdevprimary → jbcom migration (completed)
- `../CLAUDE.md` — Detailed context for Claude Code agent
- `../repository-files/initial-only/AGENTS.md` — General agent guidance
