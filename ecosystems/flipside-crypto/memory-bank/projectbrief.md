# Project Brief: FSC Control Center

## Purpose
Central orchestration repository for FlipsideCrypto infrastructure pipeline management. This repository consolidates the generator functionality from `terraform-organization` and `terraform-organization-administration` into a unified GitHub Actions-based approach.

## Core Function
1. **Centralized Pipeline Configuration** - Single source of truth for all Terraform repository pipeline configs
2. **Automated File Generation** - Generates workspace files, workflows, and configs for target repositories
3. **Cross-Repository Synchronization** - Syncs generated files to target repositories via GitHub Actions
4. **Validation** - Validates generated output matches actual repository contents

## Architecture

```
fsc-control-center
├── config/
│   ├── defaults.yaml      # Global defaults for all pipelines
│   └── pipelines.yaml     # Per-pipeline configurations
├── .github/
│   └── workflows/
│       ├── generate-pipelines.yml   # Calls reusable workflow from terraform-modules
│       └── validate-pipelines.yml   # Compares generated vs actual repo contents
├── repository-files/      # Generated files (organized by pipeline name)
│   └── {pipeline-name}/
│       └── workspaces/generator/
│           ├── pipeline.tf.json
│           └── config.tf.json
└── .github/sync.yml       # Auto-generated sync configuration
```

## Relationship to Other Repositories

### Upstream (Dependencies)
- **terraform-modules** (`FlipsideCrypto/terraform-modules`)
  - Provides reusable workflow: `.github/workflows/pipeline-generator.yml`
  - Provides composite actions: `pipeline-config`, `pipeline-files`, `pipeline-sync`
  - Enterprise action access configured for cross-org sharing

### Downstream (Managed Repositories)
All repositories in `config/pipelines.yaml`:
- terraform-aws-organization
- terraform-github-organization
- terraform-google-organization
- terraform-grafana-architecture
- terraform-aws-networking
- terraform-aws-monitoring
- terraform-aws-secretsmanager
- terraform-vault
- terraform-snowflake-architecture
- fireblocks-architecture
- compass
- terraform-aws-rstudio

### Legacy (Being Replaced)
- **terraform-organization** (`FlipsideCrypto/terraform-organization`)
  - `workspaces/generator/` - Terraform-based generator (read-only after migration)
- **terraform-organization-administration** (`fsc-internal-tooling-administration/terraform-organization-administration`)
  - `workspaces/generator/` - Terraform-based generator (read-only after migration)

## Key Benefits Over Terraform Approach

| Aspect | Terraform (Old) | GitHub Actions (New) |
|--------|-----------------|---------------------|
| Execution | `terraform apply` | GitHub workflow dispatch |
| State | S3 backend required | Stateless (file-based) |
| Triggers | Manual or release | Push, PR, or dispatch |
| Cross-org | Complex secrets sync | Enterprise action sharing |
| Visibility | Requires Terraform access | GitHub UI shows all runs |
| Debugging | Terraform logs | GitHub Actions logs |

## Success Criteria
1. Generated files match what Terraform generators produce
2. Sync creates PRs in target repositories
3. No manual intervention required for pipeline updates
4. Config changes auto-deploy via push to main
