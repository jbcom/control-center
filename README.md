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

## Domain Standard

A new standard for allocating dedicated domains to project ecosystems has been documented. See [`docs/DOMAIN-STANDARD.md`](docs/DOMAIN-STANDARD.md) for the full standard.

The `repo-config.json` schema has been updated to support an optional `domain` property for each ecosystem, and a new `docs.yml` workflow is available to automate documentation deployment with GitHub Pages.

## Historical Reference

This repo is kept as read-only for historical reference. Do not fork or clone.

---
*Archived: 2025-12-16*
