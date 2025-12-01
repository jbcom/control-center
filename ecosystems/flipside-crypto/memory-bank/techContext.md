# Technical Context

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | GitHub Actions | Workflow automation |
| Config Format | YAML | Human-readable configuration |
| File Generation | Python (inline) | Transform config to files |
| File Sync | BetaHuhn/repo-file-sync-action | Cross-repo file synchronization |
| Action Sharing | GitHub Enterprise | Cross-org internal actions |

## Dependencies

### Upstream
- **terraform-modules** repository
  - Reusable workflow: `.github/workflows/pipeline-generator.yml`
  - Composite actions: `pipeline-config`, `pipeline-files`, `pipeline-sync`
  - Python library: `lib/terraform_modules/`

### External Actions
| Action | Version | Purpose |
|--------|---------|---------|
| actions/checkout | v4 | Repository checkout |
| actions/setup-python | v5 | Python environment |
| actions/upload-artifact | v4 | Artifact storage |
| actions/download-artifact | v4 | Artifact retrieval |
| BetaHuhn/repo-file-sync-action | v1 | File synchronization |

## Secrets Configuration

| Secret | Scope | Required For |
|--------|-------|--------------|
| `FLIPSIDE_GITHUB_TOKEN` | Organization | Cross-repo access, sync PRs |
| `AWS_ACCOUNT_ID` | Organization | KMS key ARN generation |

### FLIPSIDE_GITHUB_TOKEN Permissions
- `repo` - Full repository access
- `workflow` - Workflow file updates
- `admin:org` - Organization settings (for sync)

## GitHub Enterprise Configuration

### Action Access Levels
| Repository | Visibility | Access Level |
|------------|------------|--------------|
| terraform-modules | internal | enterprise |
| fsc-control-center | internal | enterprise |

### How Enterprise Sharing Works
1. Repo has `internal` visibility (enterprise members only)
2. Repo has `access_level: enterprise` for actions
3. Other enterprise repos can reference with full path
4. No authentication needed beyond enterprise membership

## File Generation Details

### Generated Files Per Pipeline
```
repository-files/{pipeline}/
├── .gitignore
└── {root_dir}/{workspace_dir}/generator/
    ├── pipeline.tf.json     # Terraform locals for pipeline
    └── config.tf.json       # Full pipeline config as locals
```

### pipeline.tf.json Structure
```json
{
  "locals": {
    "pipeline_name": "...",
    "terraform_config": "${local.pipeline_config.terraform}",
    "terraform_workspace_config": "${local.terraform_config.workspace}",
    ...
  }
}
```

### config.tf.json Structure
```json
{
  "locals": {
    "pipeline_config": {
      "terraform": { ... },
      "kms": { ... },
      "repository": { ... }
    }
  }
}
```

## Workflow Triggers

### generate-pipelines.yml
| Trigger | Condition |
|---------|-----------|
| push | main branch, config/** paths |
| pull_request | main branch, config/** paths |
| workflow_dispatch | Manual with sync-enabled input |

### validate-pipelines.yml
| Trigger | Condition |
|---------|-----------|
| pull_request | main branch |
| workflow_dispatch | Manual with verbose input |

## Rate Limits and Quotas

| Resource | Limit | Notes |
|----------|-------|-------|
| Concurrent workflows | 20 per repo | Matrix jobs count |
| Artifact storage | 500MB per artifact | Minimal for JSON files |
| Workflow run time | 6 hours max | Usually completes in minutes |
| API calls | 5000/hour | Sync action makes API calls |

## Debugging

### View Workflow Logs
```bash
gh run view --repo FlipsideCrypto/fsc-control-center
gh run view --log --repo FlipsideCrypto/fsc-control-center
```

### Check Action Access
```bash
gh api /repos/FlipsideCrypto/terraform-modules/actions/permissions/access
```

### Manual Trigger with Verbose
```bash
gh workflow run validate-pipelines.yml \
  --repo FlipsideCrypto/fsc-control-center \
  -f verbose=true
```
