# jbcom Repository Management - Terraform Stacks

Manages all 18 jbcom repositories using Terraform Stacks for single-command plan/apply across all deployments.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          tfstacks plan / apply                               │
│                              (ONE COMMAND)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ deployment      │  │ deployment      │  │deployment│  │ deployment    │  │
│  │ "python"        │  │ "nodejs"        │  │ "go"     │  │ "terraform"   │  │
│  │ (8 repos)       │  │ (6 repos)       │  │ (2 repos)│  │ (2 repos)     │  │
│  │                 │  │                 │  │          │  │               │  │
│  │ • approvals: 0  │  │ • approvals: 0  │  │ • linear │  │ • approvals:1 │  │
│  │ • no wiki       │  │ • discussions   │  │   history│  │ • code owners │  │
│  │ • no discuss    │  │ • no wiki       │  │          │  │ • wiki        │  │
│  └────────┬────────┘  └────────┬────────┘  └────┬─────┘  └───────┬───────┘  │
│           │                    │                │                │          │
│           └────────────────────┴────────────────┴────────────────┘          │
│                                      │                                       │
│                            ┌─────────▼─────────┐                            │
│                            │ component         │                            │
│                            │ "repositories"    │                            │
│                            │ (./repository)    │                            │
│                            └─────────┬─────────┘                            │
│                                      │                                       │
│                            ┌─────────▼─────────┐                            │
│                            │ provider.github   │                            │
│                            │ "jbcom"           │                            │
│                            └───────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
terraform-stacks/
├── components.tfcomponent.hcl    # Component definition (repositories)
├── deployments.tfdeploy.hcl      # 4 deployments (python, nodejs, go, terraform)
├── providers.tfcomponent.hcl     # GitHub provider config
├── variables.tfcomponent.hcl     # Stack-level variables
├── outputs.tfcomponent.hcl       # Stack-level outputs
├── README.md
└── repository/                   # Repository component module
    ├── main.tf                   # Resources (repo, branch protection, security)
    ├── variables.tf              # Component inputs
    └── outputs.tf                # Component outputs
```

## Deployments

| Deployment | Repos | Key Settings |
|------------|-------|--------------|
| `python` | 8 | Standard config, no wiki |
| `nodejs` | 6 | Discussions enabled |
| `go` | 2 | Linear history required |
| `terraform` | 2 | 1 approval required, code owners, wiki enabled |

## Usage

### Plan ALL deployments (single command)
```bash
tfstacks plan
```

### Apply ALL deployments (single command)
```bash
tfstacks apply
```

### Plan specific deployment
```bash
tfstacks plan -deployment=python
```

## Requirements

- Terraform >= 1.14.0
- HCP Terraform Cloud account with Stacks enabled
- GitHub token with repo admin permissions

## Migration from Standard Terraform

The previous `terraform/` directory used standard Terraform with a single workspace.
This Stacks configuration provides:

1. **Single command** - Plan/apply all 18 repos at once
2. **Per-category config** - Different settings for Python vs Terraform repos
3. **Coordinated state** - All deployments managed together
4. **Better organization** - Clear separation by language/purpose

## Managed Repositories

### Python (8)
- agentic-crew
- ai_game_dev
- directed-inputs-class
- extended-data-types
- lifecyclelogging
- python-terraform-bridge
- rivers-of-reckoning
- vendor-connectors

### Node.js (6)
- agentic-control
- otter-river-rush
- otterfall
- pixels-pygame-palace
- rivermarsh
- strata

### Go (2)
- port-api
- vault-secret-sync

### Terraform (2)
- terraform-github-markdown
- terraform-repository-automation
