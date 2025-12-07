# Active Context - jbcom Control Center

## Current Status: SYNC PROCESS UPDATED

Updated sync approach with tiered propagation strategy.

### What Was Done

1. **Changed sync to direct commits** (`.github/workflows/sync.yml`)
   - Added `SKIP_PR: true` - pushes directly to main
   - No more PRs for automated sync (doesn't make sense for agent-managed repos)

2. **Implemented tiered sync approach** (`.github/sync.yml`)
   
   | Category | Behavior | Files |
   |----------|----------|-------|
   | **Rules** | Always overwrite | `core/`, `workflows/`, `languages/*.mdc` |
   | **Environment** | Initial only (`replace: false`) | `Dockerfile`, `environment.json` |
   | **Docs** | Initial only (`replace: false`) | All `docs-templates/*` |

3. **Closed vault-secret-sync PR #4**
   - Was trying to overwrite their customized Dockerfile
   - New approach respects downstream customizations

### Rationale

- **Rules**: Must stay consistent across all repos for agent behavior
- **Environment**: Repos have specific needs (Go vs Python vs Node tooling)
- **Docs**: Seed structure, then repos customize for their content

### Current Structure

```
.github/
├── sync.yml            # File sync config (tiered approach)
└── workflows/
    └── sync.yml        # Workflow (SKIP_PR: true)

cursor-rules/           # Source for sync
├── core/               # Always sync
├── languages/          # Always sync
├── workflows/          # Always sync
├── Dockerfile          # Initial only
├── environment.json    # Initial only
└── docs-templates/     # Initial only
```

## For Next Agent

1. **Trigger sync workflow** to verify new approach works
2. **Monitor downstream repos** - rules should update, Dockerfile/env should NOT

## Key Points

- Sync is now **direct to main** (no PRs)
- `replace: false` = "seed once, then leave alone"
- Rules are **always authoritative** from control center

---
*Updated: 2025-12-07*
