# Release Process

## Overview

The unified control center uses automated releases:

| Package Type | Tool | Registry | Versioning |
|--------------|------|----------|------------|
| Python | python-semantic-release | PyPI | SemVer |
| Node.js | Custom CI | npm | SemVer |
| Terraform | N/A | N/A | State-managed |

## Automated Release Flow

```
Push to main with conventional commit
         ↓
    CI runs tests
         ↓
    PSR/CI analyzes commits
         ↓
    Version bumped (if needed)
         ↓
    Git tag created
         ↓
    Package published
         ↓
    Synced to public repo
```

## Python Packages

### Trigger

Releases are triggered by conventional commits with package scopes:

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `bridge` | python-terraform-bridge |
| `connectors` | vendor-connectors |

### Version Bumps

| Commit Type | Version Bump |
|-------------|--------------|
| `fix(scope):` | Patch (0.0.X) |
| `feat(scope):` | Minor (0.X.0) |
| `feat(scope)!:` | Major (X.0.0) |
| `BREAKING CHANGE:` | Major (X.0.0) |

### Release Order

Packages release in dependency order:

1. extended-data-types (foundation)
2. lifecyclelogging
3. directed-inputs-class
4. python-terraform-bridge
5. vendor-connectors

### CI Configuration

Each package has PSR config in `pyproject.toml`:

```toml
[tool.semantic_release]
tag_format = "package-name-v{version}"
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/package_name/__init__.py:__version__"]
```

## Node.js Package (agentic-control)

### Trigger

Releases triggered when:
1. Changes detected in `packages/agentic-control/`
2. Conventional commits present since last tag

### Version Bumps

Same rules as Python:
- `fix:` → Patch
- `feat:` → Minor
- `BREAKING CHANGE` → Major

### CI Configuration

Version is determined by CI script analyzing commits since last `agentic-control-v*` tag.

## Manual Releases

### When Needed

- Emergency hotfix
- CI failure recovery
- Initial package setup

### Python Package

```bash
cd packages/<package>
uv run semantic-release version
uv run semantic-release publish
```

### Node.js Package

```bash
cd packages/agentic-control
pnpm version <patch|minor|major>
pnpm publish --access public
git tag agentic-control-v<version>
git push --tags
```

## Public Repo Sync

After release, packages sync to public repos:

| Package | Public Repo |
|---------|-------------|
| extended-data-types | jbcom/extended-data-types |
| lifecyclelogging | jbcom/lifecyclelogging |
| directed-inputs-class | jbcom/directed-inputs-class |
| python-terraform-bridge | jbcom/python-terraform-bridge |
| vendor-connectors | jbcom/vendor-connectors |
| agentic-control | jbcom/agentic-control |

Sync config in `.github/sync/<package>.yml`.

## Trusted Publishing

Both PyPI and npm use trusted publishing (OIDC):

- **PyPI**: GitHub Actions OIDC → PyPI trusted publisher
- **npm**: `--provenance` flag adds SIGSTORE attestation

No tokens stored for publishing - identity verified via OIDC.

## Troubleshooting

### "No release needed"

PSR found no conventional commits affecting the package. Check:
- Commit message format
- Package scope in commit

### "Version already exists"

Tag or version already published. Either:
- Bump version manually
- Delete tag and retry

### "Publish failed"

Check:
- Trusted publisher configured on registry
- CI has `id-token: write` permission
- Package name available

## Related

- [`.github/workflows/ci.yml`](/.github/workflows/ci.yml) - CI configuration
- [`ECOSYSTEM.toml`](/ECOSYSTEM.toml) - Package manifest
