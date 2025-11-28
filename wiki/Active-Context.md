# Active Context

## Current Focus
- **python-semantic-release Migration** - PR #213 ready to merge
- All documentation updated for new versioning approach
- PR cleanup complete, issues updated

## Completed This Session

### PR #213 - python-semantic-release Migration
Replaces pycalver with PSR for robust per-package versioning:
- Version format: `YYYYMM.MINOR.PATCH` (e.g., `202511.3.0`)
- Per-package Git tags track release state
- Conventional commits determine version bumps
- Auto-generated changelogs

### PR Cleanup
| PR | Action | Result |
|----|--------|--------|
| #215 | Closed | WIP, empty diff |
| #203 | Merged | docs: recovery summary |
| #205 | Merged | chore: MCP config |
| #204 | Closed | Needs rebase + security fixes |
| #209 | Merged | feat: file operations + exit_run |

### Issue Updates
| Issue | Status | Notes |
|-------|--------|-------|
| #210 | ✅ Closed | Resolved by PR #209 |
| #212 | Updated | RFC implemented by PR #213 |
| #214 | Open | Composite actions (future work) |

## New Versioning System

### Commit Scopes (Required)
| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

### Commit Types
| Type | Bump | Example |
|------|------|---------|
| `feat` | Minor | `feat(edt): add utility` |
| `fix`, `perf` | Patch | `fix(logging): handle error` |
| `feat!` | Major | `feat!: breaking change` |

## Documentation Updated
- README.md, CONTRIBUTING.md, CLAUDE.md
- wiki/Core-Guidelines.md (major rewrite)
- wiki/Ecosystem.md, Architecture.md, Claude.md, Copilot.md
- wiki/Agentic-Rules-Overview.md
- .amazonq/rules/jbcom-control-center.md
- .github/copilot-instructions.md, .github/copilot/instructions.md

## Next Actions
1. **Merge PR #213** - Final step (will trigger first PSR release)
2. Monitor PyPI releases with new version format
3. Verify Git tags created for each package

## Open PRs
| Repo | PR | Status | Description |
|------|-----|--------|-------------|
| jbcom/jbcom-control-center | #213 | Ready | PSR migration (MERGE LAST) |

## Open Issues
| Repo | Issue | Status | Description |
|------|-------|--------|-------------|
| jbcom/jbcom-control-center | #212 | Open | RFC - will close with PR #213 |
| jbcom/jbcom-control-center | #214 | Open | Composite actions (future) |
