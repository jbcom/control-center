# Triage Hub Guide

The **Triage Hub** is the centralized command center for managing the entire jbcom ecosystem. All AI agent operations, PR reviews, issue triage, and release coordination happen here in the private `jbcom-control-center` repository.

## Philosophy

Instead of running AI agents and managing PRs directly in public OSS repositories, we:

1. **Centralize all AI operations** - All agentic-triage commands run from this control center
2. **Maintain a single source of truth** - The `triage-hub.json` configuration defines the entire ecosystem
3. **Track dependencies** - Know exactly how packages relate to each other
4. **Coordinate releases** - Cascade updates when a dependency changes
5. **Private discussions** - AI agent conversations happen here, not in public repos

## Quick Start

### Run ecosystem health check
```bash
./scripts/ecosystem health
```

### Discover all organization repos
```bash
./scripts/ecosystem discover
```

### Sync submodules with managed repos
```bash
./scripts/ecosystem sync
```

### Triage all repos (roadmap update)
```bash
./scripts/ecosystem triage roadmap
```

### Review a PR from control center
```bash
./scripts/ecosystem triage prs review vendor-connectors 42
```

## Architecture

```
jbcom-control-center/
├── ecosystems/oss/           # All managed repos as submodules
│   ├── agentic-control/      # TypeScript: Core AI agent framework
│   ├── agentic-triage/       # TypeScript: Triage CLI (powers this hub)
│   ├── agentic-crew/         # Python: Multi-agent orchestration
│   ├── vendor-connectors/    # Python: API connectors
│   ├── strata/               # TypeScript: 3D graphics library
│   └── ...                   # All other managed repos
├── terragrunt-stacks/        # Repository configuration as code
│   ├── python/               # Python repo configs
│   ├── nodejs/               # Node.js/TypeScript repo configs
│   ├── go/                   # Go repo configs
│   └── terraform/            # Terraform module configs
├── scripts/
│   ├── ecosystem             # Main CLI
│   └── lib/ecosystem.sh      # Core library
├── triage-hub.json           # Ecosystem configuration
└── .github/workflows/
    ├── agentic-triage.yml    # Centralized triage workflow
    └── ecosystem-sync.yml    # Submodule sync workflow
```

## Configuration

### triage-hub.json

This file defines the entire ecosystem:

```json
{
  "ecosystems": {
    "python": {
      "packages": {
        "agentic-crew": {
          "description": "Multi-agent orchestration",
          "dependencies": ["lifecyclelogging", "extended-data-types"],
          "consumers": [],
          "pypi_name": "agentic-crew"
        }
      }
    }
  }
}
```

### Key fields

| Field | Description |
|-------|-------------|
| `dependencies` | Packages this one depends on (internal ecosystem) |
| `consumers` | Packages that depend on this one |
| `pypi_name` / `npm_name` | Published package name |
| `doc_url` | Documentation URL |

## Workflows

### Agentic Triage (`agentic-triage.yml`)

Runs triage operations across all managed repos:

| Trigger | Action |
|---------|--------|
| Weekly schedule | Sprint planning for all repos |
| Manual dispatch | Run any triage command |
| Issue opened | Auto-assess and label |
| PR opened | Auto-review |

### Ecosystem Sync (`ecosystem-sync.yml`)

Keeps submodules and configuration in sync:

| Trigger | Action |
|---------|--------|
| Daily schedule | Update submodules to latest |
| Push to terragrunt | Sync new repos |
| Manual dispatch | Full sync with PR |

## Commands

### Discovery

```bash
# List all repos in organization
./scripts/ecosystem discover

# JSON output
./scripts/ecosystem discover --json

# Check what's missing
./scripts/ecosystem health
```

### Triage

```bash
# Triage issues across all repos
./scripts/ecosystem triage issues

# Triage specific repo
./scripts/ecosystem triage issues vendor-connectors

# List all open PRs
./scripts/ecosystem triage prs list

# Review a PR (from control center)
./scripts/ecosystem triage prs review strata 42

# Run roadmap planning
./scripts/ecosystem triage roadmap

# Full cascade (assess + plan + review)
./scripts/ecosystem triage cascade
```

### Dependencies

```bash
# Show dependencies for a package
./scripts/ecosystem deps agentic-crew
```

### Releases

```bash
# Coordinate release (updates dependents)
./scripts/ecosystem release vendor-connectors 0.3.0
```

## Package Dependencies

The ecosystem has internal dependencies that must be considered during releases:

### Python Dependency Tree

```
lifecyclelogging (foundation)
  └── vendor-connectors
  └── python-terraform-bridge
  └── agentic-crew

extended-data-types (foundation)
  └── directed-inputs-class
  └── agentic-crew
```

### TypeScript Dependency Tree

```
agentic-control (foundation)
  └── agentic-triage

strata (foundation)
  └── rivermarsh
  └── otter-river-rush
```

## Centralized PR Management

When a PR is opened in a public repo, the triage hub can:

1. **Review it here** - Run `./scripts/ecosystem triage prs review <repo> <pr>`
2. **Track in projects** - Automatically added to Integration project
3. **Coordinate merges** - Ensure dependency order is correct
4. **Cascade updates** - Auto-create PRs in dependent repos

### Example: Reviewing a PR

```bash
# Instead of reviewing in the public repo:
cd ecosystems/oss/vendor-connectors
# ... review there ...

# Review from control center:
./scripts/ecosystem triage prs review vendor-connectors 42
```

The review comments appear in the public PR, but the AI agent conversation and decision-making happens privately here.

## GitHub Projects Integration

Two projects track the ecosystem:

### Roadmap Project
- Quarterly planning
- Feature tracking
- Release milestones

### Integration Project
- Cross-package dependencies
- Breaking changes
- Cascade updates needed

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_ORG` | GitHub organization (default: `jbdevprimary`) |
| `GH_TOKEN` | GitHub token for API access |
| `OLLAMA_API_KEY` | Ollama API key for AI operations |
| `OLLAMA_HOST` | Ollama API endpoint |
| `OLLAMA_MODEL` | AI model to use |
| `ROADMAP_PROJECT_ID` | GitHub Project ID for roadmap |
| `INTEGRATION_PROJECT_ID` | GitHub Project ID for integration |

## Adding a New Package

1. **Create the repo** in GitHub (or it already exists)

2. **Add terragrunt config**:
   ```bash
   mkdir -p terragrunt-stacks/python/new-package
   cat > terragrunt-stacks/python/new-package/terragrunt.hcl << 'EOF'
   include "root" {
     path = find_in_parent_folders()
   }
   # ... config ...
   EOF
   ```

3. **Add to triage-hub.json**:
   ```json
   "new-package": {
     "description": "Description here",
     "dependencies": [],
     "consumers": []
   }
   ```

4. **Sync submodules**:
   ```bash
   ./scripts/ecosystem sync
   ```

5. **Commit and push** - The ecosystem-sync workflow will create a PR

## Migration to jbcom

The repos are currently under `jbdevprimary` but migrating to `jbcom`. The configuration supports this:

```json
{
  "organization": "jbdevprimary",
  "migrating_to": "jbcom"
}
```

When migration is complete, update `GITHUB_ORG` everywhere.

## Troubleshooting

### Submodule not found
```bash
./scripts/ecosystem sync
```

### agentic-triage not working
```bash
npm install -g agentic-triage@latest
```

### GitHub API rate limit
```bash
gh auth status  # Check authentication
```

### Matrix generation fails
Check that `./scripts/ecosystem` is executable:
```bash
chmod +x ./scripts/ecosystem ./scripts/lib/ecosystem.sh
```
