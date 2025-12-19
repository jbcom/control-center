# Workflow Sync Process

This document explains how workflow files and other repository configuration are synced from control-center to all managed repositories.

## Overview

The control-center repository is the **single source of truth** for:
- GitHub Actions workflows
- Cursor rules and AI agent configurations
- Issue templates and PR templates
- Dependabot configuration
- Language-specific tooling configuration

Changes made in control-center are automatically synced to all managed repositories using [repo-file-sync-action](https://github.com/BetaHuhn/repo-file-sync-action).

## Architecture

```
control-center/
├── .github/
│   ├── workflows/
│   │   └── ecosystem-sync.yml  # Main sync orchestrator
│   └── sync.yml                # Sync configuration (what files → which repos)
├── repository-files/           # Files to sync to managed repos
│   ├── always-sync/            # Always overwrite in target repos
│   │   ├── .github/workflows/  # Shared workflows
│   │   └── .cursor/            # Cursor AI rules
│   ├── initial-only/           # Only sync if file doesn't exist
│   │   └── .github/dependabot.yml
│   ├── python/                 # Python-specific files
│   ├── nodejs/                 # Node.js/TypeScript files
│   ├── go/                     # Go-specific files
│   └── terraform/              # Terraform-specific files
└── repo-config.json            # Repository configuration
```

## Sync Configuration

The sync behavior is defined in `.github/sync.yml` using the repo-file-sync-action format.

### Key Concepts

| Feature | Description |
|---------|-------------|
| `source` | Path to file/directory in this repo |
| `dest` | Destination path in target repo |
| `replace: false` | Only sync if file doesn't exist (initial-only behavior) |
| `deleteOrphaned: true` | Remove files deleted from source |
| `exclude` | Glob patterns to exclude from directory sync |

### Example Configuration

```yaml
group:
  # Sync always-sync files to all repos
  - files:
      - source: repository-files/always-sync/.cursor/
        dest: .cursor/
        deleteOrphaned: true
    repos: |
      jbcom/python-agentic-crew
      jbcom/nodejs-strata

  # Sync initial-only files (only if not exists)
  - files:
      - source: repository-files/initial-only/CLAUDE.md
        dest: CLAUDE.md
        replace: false
    repos: |
      jbcom/python-agentic-crew
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
- `CLAUDE.md` - Can be customized per repo
- Environment files - Can be customized per repo

**Use for:** Templates that repos can customize after initial setup.

### Ecosystem-Specific

Files synced only to repositories in a specific ecosystem:
- `python/` → Python repositories
- `nodejs/` → Node.js/TypeScript repositories
- `go/` → Go repositories
- `terraform/` → Terraform repositories

## Authentication

The sync uses `CI_GITHUB_TOKEN` secret which is a GitHub PAT with:
- `repo` scope (full repository access)
- `workflow` scope (to update workflow files)

The token is passed to repo-file-sync-action via the `GH_PAT` input.

## Workflow Modes

### 1. PR Mode (Default for manual runs)

Creates pull requests in target repositories for review:
- Allows reviewing changes before merging
- PRs are labeled with `sync` and `automated`
- Use for careful, reviewed updates

### 2. Direct Push Mode (Scheduled/SKIP_PR)

Pushes directly to main branch:
- Used for nightly scheduled syncs
- Can be enabled manually with `skip_pr: true`
- Use for routine syncs when changes are pre-reviewed in control-center

### 3. Dry Run Mode

Previews changes without making any modifications:
- Enable with `dry_run: true`
- Useful for testing configuration changes

## Workflow Process

### 1. Automatic Sync (Nightly)

Runs at 3:00 UTC daily with direct push:
```yaml
schedule:
  - cron: '0 3 * * *'
```

### 2. Manual Sync

Trigger via GitHub UI:
1. Go to Actions → Ecosystem Sync
2. Click "Run workflow"
3. Choose options:
   - `dry_run: true` - Preview changes
   - `skip_pr: true` - Push directly instead of PRs
4. Click "Run"

### 3. On Push Sync

Automatically runs when files change:
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'repository-files/**'
      - 'repo-config.json'
      - '.github/sync.yml'
```

## Validation

### Pre-Sync Validation

Before syncing, the workflow validates:

1. **JSON Syntax**: `repo-config.json` must be valid JSON
2. **YAML Syntax**: `.github/sync.yml` must be valid YAML
3. **No Symlinks**: Fails if symlinks detected in repository-files

### Manual Validation

Run locally before committing:

```bash
# Validate JSON
./scripts/validate-config

# Check for symlinks
./scripts/check-symlinks

# Validate sync.yml
python3 -c "import yaml; yaml.safe_load(open('.github/sync.yml'))"
```

## Adding a New Repository

1. Add the repository to `repo-config.json`:

```json
{
  "ecosystems": {
    "python": {
      "repos": [
        "python-my-new-repo"
      ]
    }
  }
}
```

2. Add the repository to `.github/sync.yml` in the appropriate groups:

```yaml
group:
  - files:
      # ... existing files ...
    repos: |
      jbcom/python-agentic-crew
      jbcom/python-my-new-repo  # Add here
```

3. Commit and push:

```bash
git add repo-config.json .github/sync.yml
git commit -m "feat: add python-my-new-repo to ecosystem"
git push
```

4. The next sync will include the new repository.

## Adding/Updating Workflows

### To update a shared workflow:

1. Edit the file in `repository-files/always-sync/.github/workflows/`
2. Commit and push
3. Next sync will update all repositories (via PR or direct push)

### To add a new workflow:

1. Create the workflow in `repository-files/always-sync/.github/workflows/`
2. Add it to `.github/sync.yml` if not already covered by directory sync
3. Commit and push
4. Next sync will deploy to all repositories

### To update an ecosystem-specific workflow:

1. Edit in `repository-files/{ecosystem}/.github/workflows/`
2. Commit and push
3. Only repos in that ecosystem will receive the update

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

## Troubleshooting

### Sync Failed with "Repository not found"

**Cause**: Repository doesn't exist or access token lacks permissions.

**Solution**: 
- Verify the repository exists: `gh repo view jbcom/REPO_NAME`
- Ensure `CI_GITHUB_TOKEN` has write access to the repository
- Check token has `repo` and `workflow` scopes

### Sync Created No PRs

**Cause**: No files changed or using SKIP_PR mode.

**Solution**:
- Check workflow logs for which files were synced
- Verify changes exist in `repository-files/`
- Check if `skip_pr` was enabled

### Files Not Syncing

**Cause**: May be in `initial-only/` with `replace: false`.

**Solution**:
- Check if file exists in target repo
- If it exists, `replace: false` files won't overwrite it
- Move to `always-sync/` if you need to force updates

### PR Not Updating Existing Changes

**Cause**: Existing sync PR may need to be overwritten.

**Solution**:
- Default behavior is `OVERWRITE_EXISTING_PR: true`
- Check for existing open PRs with `sync` label
- Manually close old PRs if issues persist

## Best Practices

1. **Test with Dry-Run**: Use `dry_run: true` before applying
2. **Review PRs First**: Use PR mode for significant changes
3. **Small Changes**: Make incremental changes to limit blast radius
4. **Keep sync.yml Updated**: When adding repos, update both config files
5. **Monitor Runs**: Check sync workflow runs for failures

## Security

### Token Management

- `CI_GITHUB_TOKEN`: Organization secret with repo write access
- **Never commit tokens**: Use GitHub secrets only
- **Required Scopes**: `repo`, `workflow`
- See [Token Management](TOKEN-MANAGEMENT.md) for details

### Workflow Safety

- **SHA-Pinned Action**: repo-file-sync-action is pinned to exact commit SHA
- **Dry-Run Available**: Test before applying changes
- **PR Review Option**: Review changes before they're applied

## Related Documentation

- [Token Management](TOKEN-MANAGEMENT.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Triage Hub](TRIAGE-HUB.md)
