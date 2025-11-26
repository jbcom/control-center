# Progress Log

## Session: Nov 26, 2025

### Completed

#### CI/CD Stabilization
- [x] Fixed pycalver versioning (added v prefix to pattern)
- [x] Corrected uv workflow usage (uvx --with setuptools pycalver bump)
- [x] Fixed docs workflow (.git directory preservation)
- [x] Fixed release workflow (proper working directory for uv build)
- [x] Corrected PyPI package name: vendor-connectors (not cloud-connectors)
- [x] All 4 packages successfully publishing to PyPI

#### terraform-modules Integration
- [x] Cloned FlipsideCrypto/terraform-modules
- [x] Created branch: fix/vendor-connectors-integration
- [x] Updated pyproject.toml with vendor-connectors dependency
- [x] Deleted obsolete client files (8 files, 2,166 lines removed)
- [x] Updated imports in terraform_data_source.py, terraform_null_resource.py, utils.py
- [x] Created PR #203: https://github.com/FlipsideCrypto/terraform-modules/pull/203

#### vendor-connectors Enhancements
- [x] GoogleConnector.impersonate_subject() - API compatibility method
- [x] SlackConnector.list_usergroups() - Missing method added
- [x] AWSConnector.load_vendors_from_asm() - Lambda vendor loading
- [x] AWSConnector.get_secret() - Single secret with SecretString/Binary handling
- [x] AWSConnector.list_secrets() - Paginated listing, value fetch, empty filtering
- [x] AWSConnector.copy_secrets_to_s3() - Upload secrets dict to S3 as JSON
- [x] VaultConnector.list_secrets() - Recursive KV v2 listing with depth control
- [x] VaultConnector.get_secret() - Path handling with matchers support
- [x] VaultConnector.read_secret() - Simple single secret read
- [x] VaultConnector.write_secret() - Create/update secrets
- [x] Both use is_nothing() from extended-data-types

#### Memory Bank Infrastructure
- [x] Created .cursor/memory-bank/ structure
- [x] Documented agentic rules and workflows
- [x] Created GitHub Project for tracking
- [x] Created GitHub issues (#200, #201, #202)

### Pending
- [ ] jbcom-control-center PR #168 - vendor-connectors secrets management
- [ ] terraform-modules PR #203 CI verification
- [ ] Add deepmerge to extended-data-types (issue #201) - DONE, merged as PR #167
- [ ] Remove secrets methods from terraform-modules (after PR #168 merges)
- [ ] terraform-aws-secretsmanager refactoring
- [ ] Create merging lambda using ecosystem packages

---

## Milestones

### ✅ Milestone 1: jbcom Ecosystem PyPI Release
**Completed**: Nov 26, 2025

All packages published:
- extended-data-types
- lifecyclelogging
- directed-inputs-class
- vendor-connectors

### ✅ Milestone 2: terraform-modules Integration
**Completed**: Nov 26, 2025

PR #203 created with full vendor-connectors integration.

### 🔄 Milestone 3: Secrets Pipeline Modernization
**Status**: Not Started

Pending work in terraform-aws-secretsmanager.

---

## Technical Decisions

### Nov 26: API Compatibility Strategy
**Decision**: Add compatibility methods to vendor-connectors rather than changing terraform-modules code patterns.

**Rationale**: Less disruption to existing codebase, methods like `impersonate_subject()` are useful patterns worth keeping.

### Nov 26: Memory Bank Location
**Decision**: Place memory-bank on main branch, not feature branches only.

**Rationale**: Ensures persistence across all work, available regardless of current branch.
