# jbcom Control Center

Central control surface for managing jbcom public repositories and  infrastructure.

## What This Repo Does

1. **Syncs secrets** to all jbcom public repos (daily)
2. **Syncs cursor-rules** to all jbcom public repos (on push)
3. **Holds FSC infrastructure** (Terraform, SAM, Python libs)

## Structure

```
.
├── .github/
│   ├── sync.yml              # Sync workflow
│   └── workflows/sync.yml    # Secrets + file sync
├── cursor-rules/             # Centralized rules (synced out)
│   ├── core/                 # Fundamentals, PR workflow
│   ├── languages/            # Python, TypeScript, Go
│   ├── workflows/            # Releases, CI
│   ├── Dockerfile            # Universal dev environment
│   └── environment.json      # Cursor config
├── ecosystems//  # FSC infrastructure
│   ├── terraform/            # Modules + workspaces
│   ├── sam/                  # Lambda apps
│   └── lib/                  # Python utilities
├── docs/                     # Documentation
└── memory-bank/              # Agent context
```

## Target Repos

Secrets and cursor-rules sync to:
- `jbcom/extended-data-types`
- `jbcom/lifecyclelogging`
- `jbcom/directed-inputs-class`
- `jbcom/python-terraform-bridge`
- `jbcom/vendor-connectors`
- `jbcom/agentic-control`
- `jbcom/vault-secret-sync`
- `jbcom/cursor-rules`

## FSC Production Repos

These consume jbcom packages:
- `/terraform-modules`
- `/cluster-ops`
- `/terraform-organization-administration`

## Token Configuration

```bash
export GITHUB_JBCOM_TOKEN="..."  # jbcom repos
export GITHUB_FSC_TOKEN="..."    #  repos
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `sync.yml` | Daily schedule | Sync secrets to public repos |
| `sync.yml` | Push to cursor-rules/** | Sync files to public repos |

---

See `docs/` for detailed documentation.
