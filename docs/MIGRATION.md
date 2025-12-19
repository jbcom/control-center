# Repository Migration: jbdevprimary → jbcom

This document describes the migration process for moving repositories from the `jbdevprimary` personal account to the `jbcom` organization.

## Background

Due to GitHub issues during conversion of the personal account to an organization, many repository names were "retired". This migration creates new repositories in `jbcom` with language prefixes and performs full historical migrations.

## Naming Convention

All migrated repositories follow a language prefix convention:

| Language | Prefix | Example |
|----------|--------|---------|
| Python | `python-` | `python-extended-data-types` |
| TypeScript/Node.js | `nodejs-` | `nodejs-strata` |
| Go | `go-` | `go-secretsync` |
| Terraform | `terraform-` | `terraform-github-markdown` |

## Migration Script

The migration is performed using `scripts/migrate-to-jbcom`:

```bash
# Show migration plan
./scripts/migrate-to-jbcom plan

# Dry-run migration (no changes)
./scripts/migrate-to-jbcom migrate --dry-run

# Execute migration
./scripts/migrate-to-jbcom migrate

# Check status
./scripts/migrate-to-jbcom status
```

## Migration Categories

### Repos to Migrate (16)

**Python (8):**
- `agentic-crew` → `python-agentic-crew`
- `vendor-connectors` → `python-vendor-connectors`
- `extended-data-types` → `python-extended-data-types`
- `directed-inputs-class` → `python-directed-inputs-class`
- `lifecyclelogging` → `python-lifecyclelogging`
- `python-terraform-bridge` → `python-terraform-bridge`
- `rivers-of-reckoning` → `python-rivers-of-reckoning`
- `ai_game_dev` → `python-ai-game-dev`

**Node.js/TypeScript (6):**
- `agentic-control` → `nodejs-agentic-control`
- `strata` → `nodejs-strata`
- `otter-river-rush` → `nodejs-otter-river-rush`
- `otterfall` → `nodejs-otterfall`
- `rivermarsh` → `nodejs-rivermarsh`
- `pixels-pygame-palace` → `nodejs-pixels-pygame-palace`

**Go (1):**
- `secretsync` → `go-secretsync`

*Note: `go-port-api` and `go-vault-secret-sync` were planned but not created.*

**Terraform (2):**
- `terraform-github-markdown` → `terraform-github-markdown`
- `terraform-repository-automation` → `terraform-repository-automation`

### Already Migrated

These repos were migrated manually and are skipped:
- `control-center` (from `jbcom-control-center`)
- `agentic-triage`

### Sunset Repos (Make Private)

These repos are deprecated and will be made private instead of migrated:
- `jbcom-oss-ecosystem` - Consolidated into control-center
- `chef-selenium-grid-extras` - Old Chef recipe, no longer maintained
- `hamachi-vpn` - Old containerized VPN, no longer maintained
- `openapi-31-to-30-converter` - One-off utility

## Post-Migration Steps

After migration:

1. **Make migrated source repos private:**
   ```bash
   ./scripts/migrate-to-jbcom privatize-migrated
   ```

2. **Make sunset repos private:**
   ```bash
   ./scripts/migrate-to-jbcom privatize
   ```

3. **Update triage-hub.json** with new repository names
4. **Update repo-config.json** with new repository names
5. **Update sync configs** in `.github/sync-initial.yml` and `.github/sync-always.yml`

## Full Historical Migration

The script uses `git clone --mirror` followed by `git push --mirror` to preserve:
- All branches
- All tags
- Full commit history
- All refs

This ensures the new repository is an exact copy of the original.

## Rollback

If migration needs to be rolled back:

1. Delete the new repository in `jbcom`
2. Make the source repository in `jbdevprimary` public again

Note: Once source repos are made private, you'll need admin access to `jbdevprimary` to make them public again.
