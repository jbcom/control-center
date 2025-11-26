# Active Context

## Current Focus
jbcom ecosystem integration and CI/CD stabilization.

## Active Work

### terraform-modules Integration
- **Branch**: `fix/vendor-connectors-integration` 
- **PR**: https://github.com/FlipsideCrypto/terraform-modules/pull/203
- **Status**: Awaiting CI/review

### jbcom-control-center CI/CD
- **Branch**: `fix/vendor-connectors-pypi-name`
- **Status**: vendor-connectors enhancements pending merge

---

## GitHub Tracking

### Project
[jbcom Ecosystem Integration](https://github.com/users/jbcom/projects/2)

### Open Issues
- **terraform-modules #200**: Integrate vendor-connectors PyPI package
- **terraform-modules #201**: Add deepmerge to extended-data-types
- **terraform-modules #202**: Remove Vault/AWS secrets terraform wrappers

---

## Package Status (PyPI)

| Package | Latest | Status |
|---------|--------|--------|
| extended-data-types | 202511.x | ✅ Released |
| lifecyclelogging | 202511.x | ✅ Released |
| directed-inputs-class | 202511.x | ✅ Released |
| vendor-connectors | 202511.x | ✅ Released |

---

## Key Decisions

### Package Naming
- PyPI name: `vendor-connectors` (NOT cloud-connectors)
- Import: `from vendor_connectors import AWSConnector`

### Versioning
- CalVer: `YYYY.MM.BUILD` (e.g., 202511.42)
- Single version for entire monorepo per push
- No git tags, PyPI is source of truth

---

## Next Actions
1. Wait for terraform-modules PR #203 CI
2. Add deepmerge to extended-data-types (issue #201)
3. Clone and refactor terraform-aws-secretsmanager
4. Create merging lambda using ecosystem packages
