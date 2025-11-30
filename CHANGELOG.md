# Changelog

All notable changes to the jbcom control center.

## 2025-11-26

### Changed
- Converted to uv workspace with python-semantic-release-driven SemVer at root level
- Added `GITHUB_JBCOM_TOKEN` auth instructions to all agent configs
- Cleaned up obsolete files (ecosystem/, tools/, old workflows)

### Added
- `uv.lock` for reproducible installs
- python-semantic-release config in root `pyproject.toml`
- Workspace-level release automation (per-package detection)

### Removed
- `ecosystem/ECOSYSTEM_STATE.json` (replaced by `packages/ECOSYSTEM.toml`)
- `tools/` folder (obsolete validators/monitors)
- Old status markdown files (COMPLETE.md, MISSION_COMPLETE.md, etc.)
- Obsolete workflows (health-check.yml, hub-validation.yml, etc.)

## 2025-11-25

### Added
- Monorepo architecture with `packages/`
- `sync-packages.yml` workflow
- `release.yml` workflow for PyPI publishing
- `claude-review.yml` for pre-sync review

### Changed
- Public repos are now pure code mirrors
- All CI/review happens in control center
- Releases use `PYPI_TOKEN` directly

---

Format: [Keep a Changelog](https://keepachangelog.com/)
