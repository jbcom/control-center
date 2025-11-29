# PR Plan - Terraform Modules Migration

> **Last Updated**: 2025-11-29  
> **Status**: ✅ Agents Spawned & Coordinating  
> **Control Manager**: bc-7f35d6f6-a052-4f88-9dba-252d359b8395

## Active Fleet

| Agent ID | PR | Task |
|----------|-----|------|
| `bc-c5f87098` | #247 | directed-inputs-class decorator API |
| `bc-d21c685f` | #248 | python-terraform-bridge package |
| `bc-8b1f68c9` | #245 | vendor-connectors migration |

## PR Dependency Chain

```
PR #246: docs/wiki-orchestration-update ✅ MERGED
    ↓
PR #245: feat/complete-terraform-migration-gaps (vendor-connectors)
PR #247: feat/directed-inputs-decorator-api (independent)
PR #248: feat/python-terraform-bridge (independent)
```

## PR Links
- [PR #246](https://github.com/jbcom/jbcom-control-center/pull/246) - ✅ MERGED
- [PR #245](https://github.com/jbcom/jbcom-control-center/pull/245) - vendor-connectors Migration (100% parity)
- [PR #247](https://github.com/jbcom/jbcom-control-center/pull/247) - directed-inputs-class Decorator API
- [PR #248](https://github.com/jbcom/jbcom-control-center/pull/248) - python-terraform-bridge Package
- ~~PR #249~~ - CLOSED (redundant with #245)

---

## PR #246: Documentation & Wiki Update

**Branch**: `docs/wiki-orchestration-update`  
**Base**: `main`  
**Priority**: MERGE FIRST  
**URL**: https://github.com/jbcom/jbcom-control-center/pull/246

### Purpose
Update wiki and orchestration documentation to reflect architectural changes. This establishes the context for subsequent PRs.

### Files
- `wiki/Active-Context.md` - Current architectural state
- `wiki/Progress.md` - Session history  
- `.cursor/agents/terraform-modules-migration/ORCHESTRATION.md` - Full context
- `.cursor/agents/terraform-modules-migration/PR_PLAN.md` - This plan

### Handoff
After merge, @cursor should create PR #2 following instructions in ORCHESTRATION.md.

---

## PR #247: directed-inputs-class Decorator API

**Branch**: `feat/directed-inputs-decorator-api`  
**Base**: `main` (after PR #246 merges)  
**Depends On**: PR #246  
**URL**: https://github.com/jbcom/jbcom-control-center/pull/247

### Purpose
Add decorator-based input handling as modern alternative to inheritance.

### Files
- `packages/directed-inputs-class/src/directed_inputs_class/decorators.py` (NEW)
- `packages/directed-inputs-class/src/directed_inputs_class/__init__.py` (MODIFIED)
- `packages/directed-inputs-class/tests/test_decorators.py` (NEW)
- `packages/directed-inputs-class/README.md` (UPDATED)
- `pyproject.toml` (ruff config for package)

### Key Features
- `@directed_inputs` class decorator
- `@input_config` method decorator  
- Automatic type coercion
- Full backward compatibility

### Tests
```bash
uv run pytest packages/directed-inputs-class/tests/ -v --override-ini="addopts="
# Expected: 39 tests passing
```

### Handoff Instructions
After merge:
1. @cursor should create PR #3 (python-terraform-bridge)
2. Reference this PR as dependency
3. Use decorators from this package

---

## PR #248: python-terraform-bridge Package

**Branch**: `feat/python-terraform-bridge`  
**Base**: `main` (after PR #247 merges)  
**Depends On**: PR #247 (directed-inputs-class)  
**URL**: https://github.com/jbcom/jbcom-control-center/pull/248

### Purpose
New OSS package for Terraform ↔ Python bridging with decorator-based registration.

### Files
- `packages/python-terraform-bridge/` (NEW package)
  - `pyproject.toml`
  - `README.md`
  - `src/python_terraform_bridge/` (module_resources, registry, parameter, runtime, cli)
  - `tests/` (50 tests)
- `pyproject.toml` (workspace config)
- `uv.lock`

### Key Features
- `TerraformRegistry` with `@registry.data_source` / `@registry.null_resource`
- `TerraformModuleParameter` for type inference
- `TerraformModuleResources` for module generation
- CLI: `terraform-bridge generate/list/run`

### Tests
```bash
cd packages/python-terraform-bridge && uv run pytest tests/ -v --override-ini="addopts="
# Expected: 50 tests passing
```

### Handoff Instructions
After merge:
1. @cursor should create PR #4 (vendor-connectors migration)
2. Can also start work on terraform-modules integration

---

## PR #249: vendor-connectors Migration Functions

**Branch**: `feat/vendor-connectors-migration`  
**Base**: `main` (after PR #248 merges)  
**Depends On**: PR #248 (python-terraform-bridge)  
**URL**: https://github.com/jbcom/jbcom-control-center/pull/249

### Purpose
Complete migration of remaining functions from terraform-modules.

### Files
- `packages/vendor-connectors/src/vendor_connectors/aws/s3.py`
- `packages/vendor-connectors/src/vendor_connectors/github/__init__.py`
- `packages/vendor-connectors/src/vendor_connectors/google/billing.py`
- `packages/vendor-connectors/src/vendor_connectors/google/services.py`
- `packages/vendor-connectors/src/vendor_connectors/google/workspace.py`
- `packages/vendor-connectors/API_REFERENCE.md`
- `packages/vendor-connectors/MIGRATION_STATUS.md`

### Handoff Instructions
After merge:
1. Update terraform-modules to consume vendor-connectors + python-terraform-bridge
2. Complete remaining 4 function migrations
3. Remove deprecated code from terraform-modules

---

## Station-to-Station Handoff Protocol

Each PR should include in the body:

```markdown
## Handoff Context

📚 **Documentation**: `.cursor/agents/terraform-modules-migration/ORCHESTRATION.md`

### For @cursor

1. Read ORCHESTRATION.md for full context
2. This PR is part of the terraform-modules migration
3. After merge, create the next PR in the chain:
   - PR #246 → Merge PR #247 (directed-inputs-class)
   - PR #247 → Merge PR #248 (python-terraform-bridge)
   - PR #248 → Merge PR #249 (vendor-connectors)
4. Run tests before marking complete
5. Update wiki/Progress.md with session notes

### Dependencies
- Depends on: [previous PR if any]
- Blocks: [next PR in chain]
```

---

## Current State Summary

| Component | Status | Tests |
|-----------|--------|-------|
| directed-inputs-class decorators | ✅ Ready | 39 passing |
| python-terraform-bridge | ✅ Ready | 50 passing |
| vendor-connectors migration | ✅ Ready | existing |
| Documentation | ✅ Ready | N/A |

---

## Commands Reference

### Lint Check
```bash
uv run ruff check packages/directed-inputs-class packages/python-terraform-bridge
```

### Full Test Suite
```bash
# directed-inputs-class
uv run pytest packages/directed-inputs-class/tests/ -v --override-ini="addopts="

# python-terraform-bridge  
cd packages/python-terraform-bridge && uv run pytest tests/ -v --override-ini="addopts="
```

### Create PR with Handoff
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --title "feat(scope): Title" \
  --body "$(cat <<'EOF'
## Summary
...

## Handoff Context
📚 **Documentation**: `.cursor/agents/terraform-modules-migration/ORCHESTRATION.md`

@cursor - After merge, proceed to next PR in chain per PR_PLAN.md
EOF
)"
```
