# System Patterns

## Architecture Pattern: Config-Driven Pipeline Generation

```
┌─────────────────────────────────────────────────────────────────┐
│                        Config Layer                              │
│  config/defaults.yaml + config/pipelines.yaml                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│  .github/workflows/generate-pipelines.yml                       │
│  Calls: terraform-modules/.github/workflows/pipeline-generator  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Processing Layer                             │
│  terraform-modules composite actions:                           │
│  - pipeline-config (normalize config)                           │
│  - pipeline-files (generate files)                              │
│  - pipeline-sync (create sync config)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output Layer                                │
│  repository-files/{pipeline}/                                   │
│  .github/sync.yml                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Sync Layer                                  │
│  BetaHuhn/repo-file-sync-action                                 │
│  Creates PRs in target repositories                             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Patterns

### 1. Matrix Generation Pattern
```yaml
jobs:
  prepare:
    outputs:
      matrix: ${{ steps.parse.outputs.matrix }}
  generate:
    strategy:
      matrix: ${{ fromJson(needs.prepare.outputs.matrix) }}
```
Config is parsed into a matrix, each pipeline processed in parallel.

### 2. Artifact Collection Pattern
```yaml
generate:
  steps:
    - uses: actions/upload-artifact@v4
      with:
        name: pipeline-${{ matrix.name }}

collect:
  steps:
    - uses: actions/download-artifact@v4
      with:
        pattern: pipeline-*
```
Generated files uploaded as artifacts, collected in final job.

### 3. Enterprise Action Sharing Pattern
```yaml
# In terraform-modules (action provider)
# Set via API: access_level: enterprise

# In fsc-control-center (consumer)
uses: FlipsideCrypto/terraform-modules/.github/actions/pipeline-config@main
```
Internal repo + enterprise access = cross-org action sharing.

### 4. Reusable Workflow + Composite Actions Pattern
```yaml
# Reusable workflow references composite actions from same repo
uses: FlipsideCrypto/terraform-modules/.github/actions/pipeline-config@main
```
Both at same ref ensures consistency.

### 5. Sync Configuration Generation Pattern
```yaml
"FlipsideCrypto/terraform-aws-organization":
- dest: "workspaces/generator/pipeline.tf.json"
  source: "repository-files/terraform-aws-organization/workspaces/generator/pipeline.tf.json"
```
Sync config maps source files to destination paths.

## Configuration Structure

### defaults.yaml
```yaml
repositories:
  terraform:
    region: "us-east-1"
    backend:
      backend_bucket_name: "..."
    workspace:
      terraform_version: "1.13.1"
```

### pipelines.yaml
```yaml
pipeline-name:
  terraform:
    enabled: true
    generator:
      workspace:
        bind_to_context:
          state_path: "terraform/state/.../terraform.tfstate"
```

## Error Handling Patterns

### Graceful Degradation
- `if-no-files-found: ignore` on artifact upload
- `if: always()` on collect job
- `continue-on-error` on non-critical steps

### Validation Before Sync
- validate-pipelines.yml runs on PRs
- Compares generated vs actual before merge
- Prevents sync of incorrect files
