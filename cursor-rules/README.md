# jbcom Cursor Rules

Centralized cursor rules for the jbcom ecosystem. These rules are synced to all jbcom public repositories.

## 📦 Structure

```
cursor-rules/
├── core/                    # Core rules (always apply)
│   ├── 00-fundamentals.mdc  # Basic agent behavior
│   ├── 01-pr-workflow.mdc   # PR creation and review
│   └── 02-memory-bank.mdc   # Session memory protocol
├── languages/               # Language-specific rules
│   ├── python.mdc          # Python standards
│   ├── typescript.mdc      # TypeScript standards
│   └── go.mdc              # Go standards
├── workflows/               # Workflow rules
│   ├── releases.mdc        # Release process
│   └── ci.mdc              # CI/CD patterns
├── Dockerfile              # Universal dev environment
└── environment.json        # Cursor environment config
```

## 🔄 How Sync Works

1. **Source of Truth**: This directory in `jbcom/jbcom-control-center`
2. **Trigger**: Changes pushed to `main` on paths `cursor-rules/**`
3. **Action**: `sync.yml` workflow runs
4. **Result**: PRs created in target repos with updated files

### Target Repos

All jbcom public packages receive:
- `cursor-rules/core/` → `.cursor/rules/core/`
- `cursor-rules/languages/<lang>.mdc` → `.cursor/rules/languages/`
- `cursor-rules/workflows/` → `.cursor/rules/workflows/`
- `cursor-rules/Dockerfile` → `.cursor/Dockerfile`
- `cursor-rules/environment.json` → `.cursor/environment.json`

## ✏️ Making Changes

1. Edit files in this directory
2. Commit with descriptive message
3. Push to main
4. Sync workflow creates PRs in target repos
5. Review and merge PRs

## 🎯 Design Principles

### Rules Should Be

- **Actionable** - Tell the agent what to DO, not what to think
- **Enforceable** - Can be verified in code review
- **Minimal** - Don't over-specify, trust the agent
- **DRY** - No duplication across repos

### Language Selection

Each repo receives only relevant language rules:
- Python packages → `python.mdc`
- TypeScript packages → `typescript.mdc`
- Go packages → `go.mdc`

All repos receive core and workflow rules.

## 🔧 Dockerfile

The universal Dockerfile supports:
- **Python 3.13** with uv, ruff
- **Node.js 24** with pnpm
- **Go 1.24** with golangci-lint
- **Tools**: gh CLI, ripgrep, jq, sqlite3, etc.

## 📋 Adding a New Repo

1. Add to `.github/sync.yml`:
   ```yaml
   jbcom/new-repo:
     - source: cursor-rules/core/
       dest: .cursor/rules/core/
     - source: cursor-rules/languages/<lang>.mdc
       dest: .cursor/rules/languages/<lang>.mdc
     # ...
   ```

2. Add to `.github/workflows/sync.yml` matrix

3. Push and verify sync workflow runs

## 🔐 Related Workflows

- **sync.yml** - Unified workflow for secrets + file sync
- **ci.yml** - Uses synced configs for builds/tests

---

**Source**: jbcom/jbcom-control-center  
**Synced By**: BetaHuhn/repo-file-sync-action
