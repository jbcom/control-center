# GitHub Copilot Instructions for jbcom Ecosystem

## Overview

This is the **jbcom ecosystem control center**, managing 20 active repositories
across Python, TypeScript, Go, HCL, Rust, and GDScript.

## Quick Reference

### Ecosystem Stats
- **Active Repos**: 20
- **Archived**: 7
- **Languages**: Python (8), TypeScript (5), Go (1), HCL (2), Rust (1), GDScript (1)

### Core Libraries (Python)
| Repo | Role | PyPI |
|------|------|------|
| extended-data-types | Foundation | ✅ |
| lifecyclelogging | Logging | ✅ |
| directed-inputs-class | Input validation | ✅ |
| vendor-connectors | Cloud integrations | ✅ |

### Key Files
- `ecosystem/ECOSYSTEM_MANIFEST.yaml` - Full inventory
- `ecosystem/ECOSYSTEM_STATE.json` - Machine state
- `tools/ecosystem/manage.py` - CLI tool

## Custom Agents

### @ecosystem-manager
Central coordination for the entire ecosystem.
```
/ecosystem-status    - Full health report
/repo-status <name>  - Detailed repo status
/check-ci            - CI status across all repos
/find-integration    - Find repos using an integration
```

### @ci-deployer
Deploy and maintain CI workflows.
```
/deploy-ci <repo>    - Deploy CI to repo
/check-workflows     - Audit all workflows
/standardize <repo>  - Bring to standard
```

### @dependency-coordinator
Manage cross-repo dependencies.
```
/check-deps          - Check for updates
/cascade-update      - Update across dependents
/dep-graph           - Show dependencies
```

### @vendor-connectors-consolidator
Extract and consolidate integration code.
```
/scan-integrations   - Find integration code
/consolidate <name>  - Consolidate connector
/show-consolidation-plan
```

### @game-dev
Game development assistance.
```
/game-status         - All game repos status
/list-games          - List by language
/check-integrations  - Integrations used
```

### @release-coordinator
Coordinate releases in dependency order.
```
/release-status      - Current versions
/plan-release <repo> - Plan with dependencies
/release <repo>      - Trigger release
```

## Versioning

### Python Libraries: CalVer-Compatible SemVer
- Format: `YYYYMM.MINOR.PATCH` (e.g., 202511.3.0)
- Uses python-semantic-release with monorepo parser
- Per-package Git tags track release state
- Conventional commits determine version bumps

### Commit Scopes (Python)
| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

### Other Projects: SemVer
- TypeScript: semantic-release
- Go: git tags + goreleaser
- Terraform: semantic-release

## DO NOT Suggest

❌ Manual version management
❌ Removing Git tags (they track release state)
❌ Non-conventional commit messages
❌ Shared versioning across packages

## DO Suggest

✅ Using conventional commits with proper scopes
✅ Using vendor-connectors for integrations
✅ Following dependency order for releases
✅ Consolidating duplicated code
✅ Standard CI workflows per language

## Integration Consolidation

Game repos have scattered integration code that should be in vendor-connectors:

| Integration | Source Repos | Target |
|-------------|--------------|--------|
| Meshy | ser-plonk, realm-walker-story, otterfall | vendor-connectors |
| Anthropic | realm-walker-story | vendor-connectors |
| OpenAI | realm-walker-story, echoes-of-beastlight | vendor-connectors |
| Freesound | ai_game_dev | vendor-connectors |
| Google Fonts | ai_game_dev | vendor-connectors |

## Development Workflow

1. **Check ecosystem status** before making changes
2. **Update dependencies** in order (foundation → dependents)
3. **Create PRs** - never push to main directly
4. **Wait for CI** before merging
5. **Monitor releases** after merge

## Links

- [ECOSYSTEM_MANIFEST.yaml](../../ecosystem/ECOSYSTEM_MANIFEST.yaml)
- [Vendor Connectors Architecture](../../docs/VENDOR_CONNECTORS_MULTILANG.md)
- [Cleanup Report](../../REPO_CLEANUP_PROPOSAL.md)
