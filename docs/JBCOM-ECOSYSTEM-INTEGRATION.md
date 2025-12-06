# jbcom Ecosystem

## Overview

This control center manages the jbcom package ecosystem. All packages are developed here and synced to individual public repos.

## Packages

| Package | Type | Registry | Public Repo |
|---------|------|----------|-------------|
| extended-data-types | Python | PyPI | jbcom/extended-data-types |
| lifecyclelogging | Python | PyPI | jbcom/lifecyclelogging |
| directed-inputs-class | Python | PyPI | jbcom/directed-inputs-class |
| python-terraform-bridge | Python | PyPI | jbcom/python-terraform-bridge |
| vendor-connectors | Python | PyPI | jbcom/vendor-connectors |
| agentic-control | TypeScript | npm | jbcom/agentic-control |
| vault-secret-sync | Go | Docker Hub | jbcom/vault-secret-sync |

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

jbcom uses **Semantic Versioning (SemVer)**:
- Format: `MAJOR.MINOR.PATCH`
- Driven by conventional commits via python-semantic-release

### Version Bump Rules

| Commit Type | Bump |
|-------------|------|
| `feat(scope):` | Minor (x.Y.0) |
| `fix(scope):` | Patch (x.y.Z) |
| `feat!:` or `BREAKING CHANGE:` | Major (X.0.0) |

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

## Development

All development happens in this control center:

```
jbcom-control-center/
├── packages/                  # All packages
│   ├── extended-data-types/
│   ├── lifecyclelogging/
│   ├── directed-inputs-class/
│   ├── python-terraform-bridge/
│   ├── vendor-connectors/
│   ├── agentic-control/
│   └── vault-secret-sync/
├── cursor-rules/              # Centralized cursor rules (synced out)
├── ecosystems/flipside-crypto/ # FSC infrastructure
└── .github/workflows/         # CI/CD
```

### Conventional Commit Scopes

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `bridge` | python-terraform-bridge |
| `connectors` | vendor-connectors |
| `agentic` | agentic-control |
| `vss` | vault-secret-sync |

### Running Tests

```bash
# Install tox
uv tool install tox --with tox-uv --with tox-gh

# Run tests for a package
tox -e extended-data-types

# Run all
tox -e extended-data-types,lifecyclelogging,directed-inputs-class,python-terraform-bridge,vendor-connectors
```

### Release Process

See [RELEASE-PROCESS.md](./RELEASE-PROCESS.md)

---

**Related**: [RELEASE-PROCESS.md](./RELEASE-PROCESS.md), [TOKEN-MANAGEMENT.md](./TOKEN-MANAGEMENT.md)
