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
│   │   └── sync.yml  # Main sync orchestrator
│   └── sync.yml                # Sync configuration (what files → which repos)
├── sync-files/                 # Files to sync to managed repos
│   ├── always-sync/            # Always overwrite in target repos
│   │   ├── global/             # Shared across all repos
│   │   ├── python/             # Python-specific files
│   │   ├── nodejs/             # Node.js/TypeScript files
│   │   ├── go/                 # Go-specific files
│   │   └── terraform/          # Terraform-specific files
│   ├── initial-only/           # Only sync if file doesn't exist
│   │   ├── global/
│   │   │   └── .github/dependabot.yml
│   └── patch-sync/             # Optional files
└── repo-config.json            # Repository configuration
```

## Sync Configuration

The primary configuration file is `.github/sync.yml`. It defines mapping rules for which files in `sync-files/` go to which repositories or ecosystems.

### Directory-Based Syncing

All sync configs use **directory-based syncing** instead of individual file syncing:

✅ **Benefits:**
- **Robust**: Works even when files are added or removed from source
- **Flexible**: No config changes needed when adding new files to directories
- **Maintainable**: Fewer config entries to manage
- **Consistent**: Entire directory structures sync recursively

```yaml
# ✅ CORRECT - Directory sync (robust and flexible)
- source: sync-files/always-sync/.github/
  dest: .github/
  deleteOrphaned: false

# ❌ AVOID - Individual file sync (brittle, requires config updates)
# - source: sync-files/always-sync/.github/CODEOWNERS
#   dest: .github/CODEOWNERS
# - source: sync-files/always-sync/.github/settings.yml
#   dest: .github/settings.yml
```

**Note:** Individual file syncing should only be used for files at the root level that can't be grouped into a directory (e.g., `CLAUDE.md`, `AGENTS.md`).

### Key Config Options

| Feature | Description |
|---------|-------------|
| `source` | Path to file/directory in this repo |
| `dest` | Destination path in target repo |
| `replace: false` | Only sync if file doesn't exist |
| `deleteOrphaned: true` | Remove files deleted from source |
| `exclude` | Glob patterns to exclude from directory sync |

### Example: Sync Config

```yaml
# .github/sync.yml
jbcom/python-agentic-crew:
  - source: sync-files/always-sync/global/
    dest: ./
    deleteOrphaned: true
  - source: sync-files/always-sync/python/
    dest: ./
    deleteOrphaned: true
```

## Sync Behavior

### Always Sync (`sync-files/always-sync/`)

Files in this directory **always overwrite** target repository files.
It is organized by scope: `global`, `python`, `nodejs`, etc.

### Initial Only (`sync-files/initial-only/`)

Files are copied **only if they don't exist** in the target repository.

## Authentication

The sync uses `CI_GITHUB_TOKEN` secret which is a GitHub PAT with:
- `repo` scope (full repository access)
- `workflow` scope (to update workflow files)

The token is passed to repo-file-sync-action via the `GH_PAT` input.

## Two-Phase Sync Process

The workflow runs in two sequential phases for safety:

The workflow uses `BetaHuhn/repo-file-sync-action` which handles syncing in a single pass based on `.github/sync.yml`.

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

### 4. Selective Sync

Run only one phase via `sync_type` input:
- `both` (default) - Run both phases
- `always-only` - Skip initial sync, only run always sync
- `initial-only` - Only run initial sync for new repos

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
   - `sync_type` - Which phases to run (both/always-only/initial-only)
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
      - 'sync-files/**'
      - 'repo-config.json'
      - '.github/sync.yml'
```

## Validation

### Pre-Sync Validation

Before syncing, the workflow validates:

1. **JSON Syntax**: `repo-config.json` must be valid JSON
2. **YAML Syntax**: `.github/sync.yml` must be valid YAML
3. **No Symlinks**: Fails if symlinks detected in sync-files

### Manual Validation

Run locally before committing:

```bash
# Validate JSON
./scripts/validate-config

# Check for symlinks
./scripts/check-symlinks

# Validate sync configs
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

2. Add the repository to sync config:

```yaml
# .github/sync.yml
jbcom/python-my-new-repo:
  - source: sync-files/always-sync/global/
    dest: ./
    deleteOrphaned: true
  - source: sync-files/always-sync/python/
    dest: ./
    deleteOrphaned: true
```

3. Commit and push:

```bash
git add repo-config.json .github/sync.yml
git commit -m "feat: add python-my-new-repo to ecosystem"
git push
```

4. The next sync will:
   - Phase 1: Create initial files (CLAUDE.md, dependabot.yml, etc.)
   - Phase 2: Sync shared configs (workflows, cursor rules, etc.)

## Adding/Updating Workflows

### To update a shared workflow:

1. Edit the file in `sync-files/always-sync/global/.github/workflows/`
2. Commit and push
3. Next sync will update all repositories

### To add a new workflow:

1. Create the workflow in `sync-files/always-sync/global/.github/workflows/`
2. Commit and push
3. Next sync will deploy to all repositories

### To update an ecosystem-specific workflow:

1. Edit in `sync-files/always-sync/{ecosystem}/.github/workflows/`
2. Commit and push
3. Only repos in that ecosystem will receive the update

## Why No Symlinks?

**Symlinks must NEVER be used in sync-files/.**

### Problems with Symlinks

1. **GitHub Actions Checkout**: May not preserve symlinks
2. **rsync Behavior**: Unpredictable with symlinks
3. **Broken Links**: Target repos would receive broken symlinks
4. **Cross-Platform**: Symlinks behave differently on Windows

### Solution: Use Actual File Copies

If you need the same file in multiple places:

```bash
# ❌ WRONG - Do not use symlinks
ln -s ../global/workflow.yml sync-files/always-sync/python/.github/workflows/

# ✅ CORRECT - Copy the file
cp sync-files/always-sync/global/workflow.yml sync-files/always-sync/python/.github/workflows/
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
- Verify changes exist in `sync-files/`
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
