# jbcom Ecosystem Integration Guide

## Overview

The jbcom ecosystem provides Python packages used by FlipsideCrypto infrastructure. This guide documents how to integrate, update, and contribute to these packages.

## Package Registry

| Package | PyPI Name | Repository | Role |
|---------|-----------|------------|------|
| extended-data-types | `extended-data-types` | `jbcom/extended-data-types` | Foundation utilities |
| lifecyclelogging | `lifecyclelogging` | `jbcom/lifecyclelogging` | Structured logging |
| directed-inputs-class | `directed-inputs-class` | `jbcom/directed-inputs-class` | Input validation |
| vendor-connectors | `vendor-connectors` | `jbcom/vendor-connectors` | Cloud integrations |

## Dependency Graph

```
extended-data-types (foundation - no dependencies)
│
├── lifecyclelogging
│   └── Depends on: extended-data-types
│
├── directed-inputs-class
│   └── Depends on: extended-data-types
│
└── vendor-connectors
    └── Depends on: extended-data-types, lifecyclelogging
```

**CRITICAL**: When updating packages, follow dependency order:
1. extended-data-types (first)
2. lifecyclelogging
3. directed-inputs-class
4. vendor-connectors (last)

## Versioning

jbcom uses **CalVer-compatible Semantic Versioning**:
- Format: `YYYYMM.MINOR.PATCH`
- Example: `202511.3.0`
- Major version is calendar-based (year+month)
- Minor/patch follow semantic versioning rules

### Version Bump Rules

| Commit Type | Bump | Example |
|-------------|------|---------|
| `feat(scope):` | Minor | `202511.3.0` → `202511.4.0` |
| `fix(scope):` | Patch | `202511.3.0` → `202511.3.1` |
| `feat!:` or `BREAKING CHANGE:` | Major | `202511.3.0` → `202512.0.0` |

## Checking for Updates

### Manual Check

```bash
# Check all jbcom packages for new releases
for pkg in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  echo "=== $pkg ==="
  GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release list --repo jbcom/$pkg --limit 3
  echo ""
done
```

### Check PyPI Versions

```bash
# Check current PyPI versions
pip index versions extended-data-types
pip index versions lifecyclelogging
pip index versions directed-inputs-class
pip index versions vendor-connectors
```

### Compare with Installed

```bash
# Check installed versions vs latest
pip show extended-data-types lifecyclelogging directed-inputs-class vendor-connectors 2>/dev/null | grep -E "^(Name|Version):"
```

## Updating Dependencies

### In terraform-modules

1. **Check current versions**:
   ```bash
   grep -E "(extended-data-types|lifecyclelogging|directed-inputs-class|vendor-connectors)" requirements.txt pyproject.toml 2>/dev/null
   ```

2. **Update to new version**:
   ```bash
   # Edit requirements.txt or pyproject.toml
   # Example: extended-data-types>=202511.4.0
   ```

3. **Test integration**:
   ```bash
   pip install -e .
   pytest
   ```

4. **Create PR**:
   ```bash
   git checkout -b deps/update-jbcom-packages
   git add requirements.txt pyproject.toml
   git commit -m "deps: update jbcom packages to latest

   - extended-data-types: X.Y.Z
   - lifecyclelogging: X.Y.Z
   - vendor-connectors: X.Y.Z

   Changelog: https://github.com/jbcom/jbcom-control-center/releases"
   gh pr create --title "deps: update jbcom packages" --body "Updates jbcom ecosystem packages"
   ```

### In Other FSC Repos

Follow the same pattern, adapting to the repository's dependency management system.

## Contributing Upstream

### When to Contribute

Contribute to jbcom when:
- FSC needs a feature that would benefit the package
- FSC found a bug in a jbcom package
- FSC has an optimization that improves the package

### Contribution Process

#### 1. Clone jbcom Control Center

```bash
cd /tmp
GH_TOKEN="$GITHUB_JBCOM_TOKEN" git clone https://$GITHUB_JBCOM_TOKEN@github.com/jbcom/jbcom-control-center.git
cd jbcom-control-center
```

#### 2. Understand the Structure

```
jbcom-control-center/
├── packages/
│   ├── extended-data-types/
│   │   ├── src/extended_data_types/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── lifecyclelogging/
│   ├── directed-inputs-class/
│   └── vendor-connectors/
├── pyproject.toml          # Workspace root
├── ECOSYSTEM.toml          # Package metadata
└── .github/workflows/ci.yml
```

#### 3. Make Changes

```bash
# Create feature branch
git checkout -b feat/fsc-<feature-name>

# Make changes in appropriate package
cd packages/extended-data-types
# Edit src/, add tests

# Run tests
pytest

# Run linting
ruff check --fix src/ tests/
ruff format src/ tests/

# Run type checking
mypy src/
```

#### 4. Commit with Conventional Format

```bash
# Conventional commit with scope
git commit -m "feat(edt): add new utility function

Adds X utility needed for FSC terraform-modules pipeline generation.

- New function: do_thing()
- Tests added
- Documentation updated"
```

**Scope Reference**:
| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

#### 5. Create Pull Request

```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --repo jbcom/jbcom-control-center \
  --title "feat(edt): add new utility function" \
  --body "## Summary
Adds X utility function to extended-data-types.

## Motivation
FSC terraform-modules needs this for pipeline generation.

## Changes
- Added \`do_thing()\` function
- Added unit tests
- Updated documentation

## Test Plan
- [x] Unit tests pass
- [x] Lint passes (ruff)
- [x] Type check passes (mypy)

## FSC Integration
After merge and release, will be consumed by:
- FlipsideCrypto/terraform-modules

---
*Contributed by FSC Control Center*"
```

#### 6. Track in FSC

```bash
# Create tracking issue in FSC
gh issue create \
  --repo FlipsideCrypto/fsc-control-center \
  --title "🔗 Upstream: jbcom PR #<number>" \
  --body "Tracking upstream contribution to jbcom.

**PR**: https://github.com/jbcom/jbcom-control-center/pull/<number>
**Package**: extended-data-types
**Feature**: <description>

## Status
- [ ] PR created
- [ ] PR reviewed
- [ ] PR merged
- [ ] Released to PyPI
- [ ] FSC updated to use new version"
```

## Monitoring jbcom Health

### Repository Status

```bash
# Control center health
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api /repos/jbcom/jbcom-control-center --jq '{
  open_issues: .open_issues_count,
  open_prs: .open_issues_count,
  last_push: .pushed_at
}'

# CI status
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/jbcom-control-center --limit 5
```

### Package Release Status

```bash
# Check each package's latest release
for pkg in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  echo "=== $pkg ==="
  GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release view --repo jbcom/$pkg --json tagName,publishedAt,name 2>/dev/null || echo "No releases"
done
```

## Troubleshooting

### Import Errors

If you see import errors after updating:

```python
# Check installed version
import extended_data_types
print(extended_data_types.__version__)

# Check what's available
dir(extended_data_types)
```

### Version Conflicts

If packages have conflicting version requirements:

```bash
# Check dependency tree
pip show extended-data-types --verbose | grep Requires
pip show vendor-connectors --verbose | grep Requires

# Check for conflicts
pip check
```

### jbcom Wiki Reference

For detailed jbcom documentation:
- Core Guidelines: https://github.com/jbcom/jbcom-control-center/wiki/Core-Guidelines
- Python Standards: https://github.com/jbcom/jbcom-control-center/wiki/Python-Standards
- PR Ownership: https://github.com/jbcom/jbcom-control-center/wiki/PR-Ownership

---

**Last Updated**: 2025-11-28  
**jbcom Wiki**: https://github.com/jbcom/jbcom-control-center/wiki
