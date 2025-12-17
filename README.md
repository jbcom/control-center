# ⚠️ ARCHIVED - Migrated to jbcom/.github

This repository has been archived. All functionality has been migrated to:

**[jbcom/.github](https://github.com/jbcom/.github)** (private)

## What Moved Where

| Component | New Location |
|-----------|--------------|
| Agent memory bank | `.github/memory-bank/` |
| File sync templates | `.github/sync-files/` |
| Cursor rules | `.github/sync-files/*/cursor/rules/` |
| Workflow templates | `.github/sync-files/always-sync/.github/workflows/` |
| Repo settings | `settings.yml` (via Settings app) |

## New Architecture

- **Settings app** handles repository configuration declaratively
- **File sync workflow** creates PRs to sync files to repos
- **No more custom scripts** - everything is YAML-based

## Historical Reference

This repo is kept as read-only for historical reference. Do not fork or clone.

---
*Archived: 2025-12-16*
