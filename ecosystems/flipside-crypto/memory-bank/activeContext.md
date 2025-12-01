# Active Context

## Current State: AGENTIC CONTROL CONFIGURED

Complete agentic control system configured for FlipsideCrypto ecosystem. Agent fleet ready for orchestrated operations across all repositories.

### Repository Structure

```
fsc-control-center/
├── config/
│   ├── defaults.yaml          # terraform_version: 1.13.1, python: 3.13.5
│   ├── pipelines.yaml         # 13 pipeline definitions
│   ├── state-paths.yaml       # 41 workspaces with state keys (REGENERATED FROM REALITY)
│   └── secrets/
├── terraform/
│   ├── modules/               # 30 module categories (aws, google, terraform, etc.)
│   └── workspaces/
│       ├── terraform-aws-organization/    # 37 config.tf.json files
│       └── terraform-google-organization/ # 7 config.tf.json files
├── scripts/
│   └── audit-workspace-generation.py      # Workspace audit tool
└── reports/workspace-audit/               # Audit results
```

### Workspace Breakdown

**41 workspaces with valid state keys** tracked in state-paths.yaml:
- terraform-aws-organization: 34 workspaces
- terraform-google-organization: 7 workspaces

**3 template files** (no state key, intermediate/template):
- workers-stg/rpc, workers-stg/workers, workers-stg/rpc-stg

### State Key Pattern

`terraform/state/{pipeline}/workspaces/{workspace}/terraform.tfstate`

Examples:
- `terraform/state/terraform-aws-organization/workspaces/generator/terraform.tfstate`
- `terraform/state/compass/workspaces/infrastructure/terraform.tfstate`
- `terraform/state/terraform-google-organization/workspaces/gcp/projects/terraform.tfstate`

### Backend Config (from actual config.tf.json)

```
bucket: flipside-crypto-internal-tooling
dynamodb_table: internal-tooling-terraform-state
region: us-east-1
encrypt: true
```

### Critical Constraint

**State keys are IMMUTABLE** - state-paths.yaml is the authoritative registry.

### What's Working

- ✅ All 44 config.tf.json files are valid JSON
- ✅ state-paths.yaml regenerated from actual workspace structure
- ✅ Audit system tracks workspace state/hash/providers
- ✅ Terraform 1.13.1 installed (matching defaults.yaml)

### What's Next

- Build new generator that produces ZERO DIFF against existing config.tf.json
- Test terraform init/validate on workspaces (requires module access)
- Copy remaining managed repos (terraform-github-organization, etc.) if needed

### Recent Session Progress

**Completed:**
- Regenerated state-paths.yaml from actual workspace structure (was wrong)
- Cleaned up terragrunt placeholder directories
- Fixed HCL formatting errors in terraform-google-organization
- Created shim modules for terraform_modules → vendor-connectors compatibility
- Got tm_cli working (`pip install -e .` + shims)
- Updated ECOSYSTEM.toml to reflect actual state

**Python Shims Created:**
- logging.py - wraps lifecyclelogging.Logging with old interface
- aws_client.py, github_client.py, google_client.py, slack_client.py, vault_client.py, zoom_client.py - wrap vendor_connectors
- doppler_config.py, vault_config.py - configuration constants

**Key Discovery:**
- defaults.yaml has terraform_version: 1.13.1, python_version: 3.13.5
- Must review ALL config files when taking ownership of a codebase
