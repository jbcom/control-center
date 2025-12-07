# jbcom Control Center

Central control surface for managing jbcom public repositories and FlipsideCrypto infrastructure.

## What This Repo Does

1. **Syncs secrets** to all jbcom public repos (daily)
2. **Syncs repository files** to all jbcom public repos (on push)
3. **Holds FSC infrastructure** (Terraform, SAM, Python libs)

## Structure

```
.
├── .github/
│   ├── sync.yml              # File sync config
│   └── workflows/sync.yml    # Secrets + file sync workflow
├── repository-files/         # Files synced to target repos
│   ├── always-sync/          # Rules (always overwrite)
│   │   └── .cursor/rules/
│   ├── initial-only/         # Scaffold (sync once, repos customize)
│   │   ├── .cursor/          # Dockerfile, environment.json
│   │   ├── .github/          # Workflow files
│   │   └── docs/             # Documentation scaffold
│   ├── python/               # Python language rules
│   ├── nodejs/               # Node.js/TypeScript language rules
│   └── go/                   # Go language rules
├── ecosystems/flipside-crypto/  # FSC infrastructure
│   ├── terraform/            # Modules + workspaces
│   ├── sam/                  # Lambda apps
│   └── lib/                  # Python utilities
├── docs/                     # Documentation
└── memory-bank/              # Agent context
```

## Target Repos

Secrets and repository files sync to:
- `jbcom/extended-data-types`
- `jbcom/lifecyclelogging`
- `jbcom/directed-inputs-class`
- `jbcom/python-terraform-bridge`
- `jbcom/vendor-connectors`
- `jbcom/agentic-control`
- `jbcom/vault-secret-sync`

## Sync Behavior

| Directory | Behavior | Contents |
|-----------|----------|----------|
| `always-sync/` | Always overwrite | Cursor rules (must stay consistent) |
| `initial-only/` | Sync once (`replace: false`) | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/` | Always overwrite | Language-specific rules |

## FSC Production Repos

These consume jbcom packages:
- `FlipsideCrypto/terraform-modules`
- `fsc-platform/cluster-ops`
- `fsc-internal-tooling-administration/terraform-organization-administration`

## Token Configuration

```bash
export GITHUB_JBCOM_TOKEN="..."  # jbcom repos
export GITHUB_FSC_TOKEN="..."    # FlipsideCrypto repos
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `sync.yml` | Daily schedule | Sync secrets to public repos |
| `sync.yml` | Push to main | Sync files to public repos |

---

See `docs/` for detailed documentation.
