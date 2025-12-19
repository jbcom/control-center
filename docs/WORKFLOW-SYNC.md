# Workflow Sync Process

This document explains how workflow files and other repository configuration are synced from control-center to all managed repositories.

## Overview

The control-center repository is the **single source of truth** for:
- GitHub Actions workflows
- Cursor rules and AI agent configurations
- Issue templates and PR templates
- Dependabot configuration
- Language-specific tooling configuration

Changes made in control-center are automatically synced to all managed repositories.

## Architecture

```
control-center/
├── .github/workflows/        # Control center workflows (NOT synced)
│   ├── ecosystem-sync.yml   # Main sync orchestrator
│   └── lint-config.yml      # Config validation
├── repository-files/        # Files to sync to managed repos
│   ├── always-sync/         # Always overwrite in target repos
│   │   ├── .github/workflows/   # Shared workflows
│   │   └── .cursor/             # Cursor AI rules
│   ├── initial-only/        # Only sync if file doesn't exist
│   │   └── .github/dependabot.yml
│   ├── python/              # Python-specific files
│   ├── nodejs/              # Node.js/TypeScript files
│   ├── go/                  # Go-specific files
│   └── terraform/           # Terraform-specific files
└── repo-config.json         # Repository configuration
```

## Sync Behavior

### Always Sync (`always-sync/`)

Files in this directory **always overwrite** target repository files:
- `.github/workflows/*.yml` - Shared workflow files
- `.cursor/*` - Cursor AI rules
- `.github/CODEOWNERS` - Code ownership rules

**Use for:** Files that must remain consistent across all repositories.

### Initial Only (`initial-only/`)

Files are copied **only if they don't exist** in the target repository:
- `.github/dependabot.yml` - Allows repo-specific configuration
- Environment files - Can be customized per repo

**Use for:** Templates that repos can customize after initial setup.

### Ecosystem-Specific

Files synced only to repositories in a specific ecosystem:
- `python/` → Python repositories
- `nodejs/` → Node.js/TypeScript repositories
- `go/` → Go repositories
- `terraform/` → Terraform repositories

## Configuration

### repo-config.json

```json
{
  "ecosystems": {
    "python": {
      "repos": [
        "python-agentic-crew",
        "python-vendor-connectors"
      ]
    },
    "nodejs": {
      "repos": [
        "nodejs-strata",
        "nodejs-agentic-control"
      ]
    }
  }
}
```

Each ecosystem lists the repositories that belong to it. The sync process:
1. Syncs `always-sync/` files to all repos
2. Syncs ecosystem-specific files (e.g., `python/`) to repos in that ecosystem
3. Syncs `initial-only/` files only if they don't exist

## Why No Symlinks?

**Symlinks must NEVER be used in repository-files/.**

### Problems with Symlinks

1. **GitHub Actions Checkout**: May not preserve symlinks
2. **rsync Behavior**: Unpredictable with symlinks
3. **Broken Links**: Target repos would receive broken symlinks
4. **Cross-Platform**: Symlinks behave differently on Windows

### Solution: Use Actual File Copies

If you need the same file in multiple places:

```bash
# ❌ WRONG - Do not use symlinks
ln -s ../shared/workflow.yml repository-files/python/.github/workflows/

# ✅ CORRECT - Copy the file
cp repository-files/shared/workflow.yml repository-files/python/.github/workflows/
```

The small cost of maintaining duplicate files is vastly outweighed by the reliability gains.

## Workflow Process

### 1. Automatic Sync (Nightly)

Runs at 3:00 UTC daily:
```yaml
schedule:
  - cron: '0 3 * * *'
```

### 2. Manual Sync

Trigger via GitHub UI:
1. Go to Actions → Ecosystem Sync
2. Click "Run workflow"
3. Optionally specify a single target repo
4. Enable dry-run to preview changes

### 3. On Push Sync

Automatically runs when files change:
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'repository-files/**'
      - 'repo-config.json'
```

## Validation

### Pre-Sync Validation

Before syncing, the workflow validates:

1. **JSON Syntax**: `repo-config.json` must be valid JSON
2. **No Trailing Commas**: Strictly enforced
3. **Required Structure**: All required keys must exist
4. **No Symlinks**: Fails if symlinks detected

### Manual Validation

Run locally before committing:

```bash
# Validate JSON
./scripts/check-symlinks

# Check workflow consistency
./scripts/check-workflow-consistency

# Validate JSON structure
jq empty repo-config.json
```

## Adding a New Repository

1. Add the repository to the appropriate ecosystem in `repo-config.json`:

```json
{
  "ecosystems": {
    "python": {
      "repos": [
        "python-my-new-repo"  // Add here
      ]
    }
  }
}
```

2. Commit and push:

```bash
git add repo-config.json
git commit -m "feat: add python-my-new-repo to ecosystem"
git push
```

3. The next sync (or manual trigger) will include the new repository.

## Adding/Updating Workflows

### To update a shared workflow:

1. Edit the file in `repository-files/always-sync/.github/workflows/`
2. Commit and push
3. Next sync will update all repositories

### To add a new workflow:

1. Create the workflow in `repository-files/always-sync/.github/workflows/`
2. Test it locally in control-center's `.github/workflows/` (optional)
3. Commit and push
4. Next sync will deploy to all repositories

### To update an ecosystem-specific workflow:

1. Edit in `repository-files/{ecosystem}/.github/workflows/`
2. Commit and push
3. Only repos in that ecosystem will receive the update

## Troubleshooting

### Sync Failed with "Repository not found"

**Cause**: Repository doesn't exist or access token lacks permissions.

**Solution**: 
- Verify the repository exists: `gh repo view jbcom/REPO_NAME`
- Ensure `CI_GITHUB_TOKEN` has write access

### Sync Skipped All Repositories

**Cause**: Matrix generation failed (JSON structure error).

**Solution**:
- Check workflow logs for "Build Repo Matrix" step
- Validate `repo-config.json` structure
- Run: `jq '.ecosystems | to_entries[] | .value.repos[]' repo-config.json`

### Symlink Error

**Cause**: Symlink detected in repository-files/.

**Solution**:
```bash
# Find symlinks
./scripts/check-symlinks

# Replace with actual files
rm repository-files/python/.github/workflows/symlink.yml
cp source-file.yml repository-files/python/.github/workflows/workflow.yml
```

### Files Not Syncing

**Cause**: May be in `initial-only/` directory.

**Solution**:
- Check if file exists in target repo
- If it exists, `initial-only/` files won't overwrite it
- Move to `always-sync/` if you need to force updates

## Best Practices

1. **Test Workflows Locally**: Always test workflow changes in a single repo first
2. **Use Dry-Run**: Test sync with `dry_run: true` before applying
3. **Small Changes**: Make incremental changes to limit blast radius
4. **Monitor Runs**: Check sync workflow runs for failures
5. **Keep Docs Updated**: Update this document when changing sync behavior

## Security

### Token Management

- `CI_GITHUB_TOKEN`: Organization secret with repo write access
- **Never commit tokens**: Use GitHub secrets only
- **Least Privilege**: Token only has repo-level permissions

### Workflow Safety

- **Non-Fast-Fail**: Continues syncing even if one repo fails
- **Max Parallel**: Limited to 5 simultaneous syncs
- **Dry-Run Available**: Test before applying changes

## Related Documentation

- [Token Management](TOKEN-MANAGEMENT.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Triage Hub](TRIAGE-HUB.md)
