# FSC Control Center - Monorepo Architecture

## Design Principle

**One repo. One PR. One release.**

The control center agent should have direct access to ALL infrastructure code. No cross-repo coordination. No "update terraform-modules, then terraform-organization, then sync to managed repos."

## Target Structure

```
fsc-control-center/
├── packages/                          # TypeScript/Python tooling
│   ├── agentic-control/               # Agent orchestration toolkit
│   ├── pipeline-generator/            # Workflow generation
│   └── secrets-manager/               # Secrets lambda (Go)
│
├── terraform/
│   ├── modules/                       # Reusable Terraform modules
│   │   ├── aws/
│   │   │   ├── lambda/
│   │   │   ├── iam/
│   │   │   ├── s3/
│   │   │   ├── secrets-manager/
│   │   │   └── ...
│   │   ├── google/
│   │   │   ├── cloud-function/
│   │   │   ├── secret-manager/
│   │   │   └── ...
│   │   └── github/
│   │       ├── repository/
│   │       ├── team/
│   │       └── ...
│   │
│   └── workspaces/                    # All workspace configurations
│       ├── _bootstrap/                # Genesis - creates everything else
│       │   ├── main.tf
│       │   ├── providers.tf
│       │   └── outputs.tf
│       │
│       ├── organization/              # GitHub org settings, teams, repos
│       │   ├── main.tf
│       │   ├── repositories.tf        # ALL managed repo definitions
│       │   └── outputs.tf
│       │
│       ├── aws-core/                  # Core AWS infrastructure
│       │   ├── main.tf
│       │   └── outputs.tf
│       │
│       ├── google-core/               # Core GCP infrastructure
│       │   ├── main.tf
│       │   └── outputs.tf
│       │
│       └── pipelines/                 # Per-repo pipeline workspaces
│           ├── compass/
│           │   ├── main.tf            # Binds to org context
│           │   ├── pipeline.tf        # Pipeline-specific resources
│           │   └── outputs.tf
│           ├── livequery-models/
│           ├── external-models/
│           └── .../
│
├── config/
│   ├── pipelines.yaml                 # Pipeline definitions
│   ├── repositories.yaml              # Managed repo registry
│   └── defaults.yaml                  # Default configurations
│
├── .github/
│   └── workflows/
│       ├── terraform-plan.yml         # Plan on PR
│       ├── terraform-apply.yml        # Apply on merge
│       ├── release.yml                # Coordinated releases
│       └── sync-repos.yml             # Push generated files to repos
│
├── .cursor/
│   ├── rules/                         # Agent instructions
│   └── scripts/                       # Agent tooling
│
├── memory-bank/                       # Agent continuity
├── ECOSYSTEM.toml                     # Dependency graph
├── pnpm-workspace.yaml               # Package management
└── terragrunt.hcl                    # Workspace orchestration
```

## Key Changes from Current State

### Eliminated Repos

| Old Repo | Where It Goes |
|----------|---------------|
| terraform-modules | `terraform/modules/` |
| terraform-organization | `terraform/workspaces/organization/` |
| Per-repo generator workspaces | `terraform/workspaces/pipelines/<repo>/` |

### What Stays in Managed Repos

Managed repos (compass, livequery-models, etc.) keep ONLY:
- `.github/workflows/*.yml` - Generated, calls back to control center
- Application code
- Repo-specific configs

They do NOT have:
- Terraform state
- Module definitions
- Pipeline definitions

### Context Chaining

```hcl
# terraform/workspaces/pipelines/compass/main.tf

# Bind to organization context
data "terraform_remote_state" "org" {
  backend = "s3"
  config = {
    bucket = "fsc-terraform-state"
    key    = "workspaces/organization/terraform.tfstate"
  }
}

# Inherit context
locals {
  org_context = data.terraform_remote_state.org.outputs
  repo_config = local.org_context.repositories["compass"]
}

# Pipeline resources use inherited context
module "pipeline" {
  source = "../../../modules/aws/pipeline"
  
  repository    = local.repo_config
  environments  = local.org_context.environments
  # ... everything flows from org context
}
```

## Workflow

### Making a Change

**Before (fragmented):**
1. PR to terraform-modules
2. Wait for merge
3. PR to terraform-organization
4. Wait for merge
5. Run generator
6. PRs to N managed repos
7. Wait for all merges

**After (monorepo):**
1. PR to fsc-control-center
2. Merge
3. Done (sync workflow pushes to managed repos if needed)

### Release Coordination

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
    steps:
      - name: Build packages
        run: pnpm -r build
        
      - name: Terraform plan all workspaces
        run: |
          for workspace in terraform/workspaces/*/; do
            terragrunt plan -chdir="$workspace"
          done
          
      - name: Apply on approval
        run: terragrunt run-all apply
        
      - name: Sync to managed repos
        run: pnpm exec pipeline-generator sync --all
        
      - name: Publish packages
        run: pnpm -r publish
```

## Agent Benefits

With this structure, the FSC control center agent can:

1. **See everything** - All modules, workspaces, configs in one place
2. **Change anything** - Single PR for any infrastructure change
3. **Test holistically** - `terragrunt plan` shows full impact
4. **Release atomically** - One tag releases everything
5. **Reason about dependencies** - ECOSYSTEM.toml + terragrunt graph

### Example Agent Task

"Add a new managed repository called 'new-data-pipeline'"

**Agent actions (all in one PR):**
```bash
# 1. Add to config
echo "new-data-pipeline:" >> config/repositories.yaml

# 2. Add organization resource
# Edit terraform/workspaces/organization/repositories.tf

# 3. Create pipeline workspace
mkdir -p terraform/workspaces/pipelines/new-data-pipeline
# Create main.tf, pipeline.tf, outputs.tf

# 4. Generate initial workflows
pnpm exec pipeline-generator generate new-data-pipeline

# 5. Commit, push, PR - DONE
```

## Migration Path

### Phase 1: Structure (Week 1)
- Create `terraform/` directory structure
- Set up terragrunt.hcl
- Add pnpm workspace

### Phase 2: Modules (Week 2)
- Copy modules from terraform-modules
- Update source paths
- Verify with `terraform validate`

### Phase 3: Workspaces (Week 3)
- Migrate organization workspace
- Import existing state
- Set up remote state references

### Phase 4: Pipeline Workspaces (Week 4)
- Create workspace per managed repo
- Import existing state
- Update context bindings

### Phase 5: Deprecation (Week 5)
- Archive terraform-modules
- Archive terraform-organization
- Update managed repo workflows to reference control center

## Terraform Stacks Approach (CI/CD Native)

**Key insight**: The old terragrunt/individual-workspace pattern was human-oriented. Humans have local auth and can run `terraform plan` on single workspaces. Agents don't - we rely on CI/CD.

### The Simpler Pattern

```
Agent pushes code
    │
    ▼
┌─────────────────────────────────────────┐
│  terraform-stacks.yml                   │
│                                         │
│  1. Parse state-paths.yaml              │
│  2. Order workspaces by layer           │
│  3. terraform plan (ALL workspaces)     │
│  4. Post summary to PR                  │
│                                         │
│  ─────── APPROVAL GATE ───────          │
│                                         │
│  5. terraform apply (ALL workspaces)    │
└─────────────────────────────────────────┘
```

### Why This Is Better for Agents

| Old (Human) | New (Agent) |
|-------------|-------------|
| Run `terraform plan` locally | Push code, workflow runs plan |
| Target single workspace | Plan ALL workspaces at once |
| Terragrunt for orchestration | GitHub Actions + state-paths.yaml |
| Manual approval per workspace | Single approval gate |
| Complex dependency management | Layer ordering from YAML |

### Eliminated

- ❌ Terragrunt
- ❌ Individual workspace targeting
- ❌ Local Terraform auth
- ❌ Complex CLI orchestration

### Kept

- ✅ State paths (IMMUTABLE) in state-paths.yaml
- ✅ Layer ordering for dependency respect
- ✅ Backend configuration per workspace
- ✅ Approval gates before apply

## State Management - CRITICAL

### ⚠️ ZERO TOLERANCE: State Paths Must Be Preserved

**The location of HCL files can change. The state path CANNOT.**

When migrating workspaces, the backend configuration MUST preserve the exact state path that exists today. The S3 key (or equivalent) is the identity of the workspace.

### State Path Mapping

Each workspace declares its ORIGINAL state path explicitly:

```hcl
# terraform/workspaces/organization/backend.tf
terraform {
  backend "s3" {
    bucket         = "fsc-terraform-state"
    key            = "terraform-organization/terraform.tfstate"  # ORIGINAL PATH - DO NOT CHANGE
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "fsc-terraform-locks"
  }
}
```

```hcl
# terraform/workspaces/pipelines/compass/backend.tf
terraform {
  backend "s3" {
    bucket         = "fsc-terraform-state"
    key            = "compass/pipeline/terraform.tfstate"  # ORIGINAL PATH - DO NOT CHANGE
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "fsc-terraform-locks"
  }
}
```

### State Path Registry

Maintain an explicit registry of state paths:

```yaml
# config/state-paths.yaml
# AUTHORITATIVE MAPPING - HCL location → State path
# Changing state paths requires explicit state migration

workspaces:
  organization:
    hcl_path: terraform/workspaces/organization
    state_key: terraform-organization/terraform.tfstate
    migrated_from: github.com/FlipsideCrypto/terraform-organization
    
  aws-core:
    hcl_path: terraform/workspaces/aws-core
    state_key: aws-core/terraform.tfstate
    
  pipelines/compass:
    hcl_path: terraform/workspaces/pipelines/compass
    state_key: compass/pipeline/terraform.tfstate
    migrated_from: github.com/FlipsideCrypto/compass/.terraform
    
  pipelines/livequery-models:
    hcl_path: terraform/workspaces/pipelines/livequery-models
    state_key: livequery-models/pipeline/terraform.tfstate
```

### Terragrunt with Explicit State Keys

```hcl
# terragrunt.hcl (root)
locals {
  # Load state path registry
  state_paths = yamldecode(file("${get_repo_root()}/config/state-paths.yaml"))
  
  # Get workspace name from path
  workspace_name = replace(path_relative_to_include(), "terraform/workspaces/", "")
  
  # Look up the ORIGINAL state key - this is immutable
  state_key = local.state_paths.workspaces[local.workspace_name].state_key
}

remote_state {
  backend = "s3"
  config = {
    bucket         = "fsc-terraform-state"
    key            = local.state_key  # EXPLICIT - never derived from path
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "fsc-terraform-locks"
  }
}
```

### Migration Checklist

For EACH workspace being consolidated:

- [ ] Document current state path in `config/state-paths.yaml`
- [ ] Verify state exists: `aws s3 ls s3://bucket/path/terraform.tfstate`
- [ ] Create workspace directory with backend.tf using EXACT state path
- [ ] Run `terraform init` - should say "Reusing previous state"
- [ ] Run `terraform plan` - should show NO changes (or only expected drift)
- [ ] If plan shows destroy/create on existing resources: **STOP - state path mismatch**

### Validation

```bash
#!/bin/bash
# scripts/validate-state-paths.sh
# Run before ANY terraform operation after migration

set -e

for workspace in terraform/workspaces/*/; do
  name=$(basename "$workspace")
  
  # Get declared state key from backend.tf
  declared_key=$(grep -oP 'key\s*=\s*"\K[^"]+' "$workspace/backend.tf")
  
  # Get expected key from registry
  expected_key=$(yq ".workspaces[\"$name\"].state_key" config/state-paths.yaml)
  
  if [ "$declared_key" != "$expected_key" ]; then
    echo "❌ CRITICAL: State path mismatch for $name"
    echo "   Declared: $declared_key"
    echo "   Expected: $expected_key"
    exit 1
  fi
  
  # Verify state actually exists
  if ! aws s3 ls "s3://fsc-terraform-state/$declared_key" > /dev/null 2>&1; then
    echo "⚠️  WARNING: No existing state at $declared_key (new workspace?)"
  fi
done

echo "✅ All state paths validated"
```

### What NEVER Happens

```hcl
# ❌ NEVER derive state key from HCL file path
key = "${path_relative_to_include()}/terraform.tfstate"

# ❌ NEVER use workspace name that differs from original
key = "control-center/workspaces/${local.workspace}/terraform.tfstate"

# ❌ NEVER change state key without explicit state migration
# Old: "compass/pipeline/terraform.tfstate"  
# New: "pipelines/compass/terraform.tfstate"  # THIS ORPHANS RESOURCES
```

### If State Migration IS Needed

Only with explicit approval and process:

```bash
# 1. Lock the workspace
# 2. Document in state-paths.yaml with migration note
# 3. Use terraform state commands
terraform init -migrate-state \
  -backend-config="key=NEW_PATH/terraform.tfstate"
# 4. Verify all resources still tracked
terraform plan  # Must show no unexpected changes
# 5. Update state-paths.yaml with new path
# 6. Remove old state file
```

## What This Enables

1. **Instant context** - Agent reads one repo, understands all infrastructure
2. **Fearless changes** - Full plan shows all downstream effects
3. **Coordinated releases** - Tag once, release everything
4. **No sync hell** - Changes propagate automatically
5. **True ownership** - Control center controls everything
