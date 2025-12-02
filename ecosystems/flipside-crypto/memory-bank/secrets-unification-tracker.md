# Secrets Infrastructure Unification Tracker

## Status: Active Proposal

**Master Proposal**: https://github.com/FlipsideCrypto/data-platform-secrets-syncing/blob/main/PROPOSAL.md

## Overview

Consolidating secrets syncing/merging from 3 repos into unified architecture with vault-secret-sync.

## All PRs Created

### data-platform-secrets-syncing (Greenfielded)

| PR | Branch | Description | Status |
|----|--------|-------------|--------|
| - | `archive/pre-greenfield-20251201` | Archived previous content | ✅ Done |
| - | `main` | Greenfielded with README + PROPOSAL.md | ✅ Done |
| #43 | `proposal/vault-secret-sync` | Kustomize manifests for vault-secret-sync | 🔄 Open |
| #44 | `proposal/sam-approach-fixed` | SAM Lambda approach | 🔄 Open |

### terraform-aws-secretsmanager

| PR | Description | Status |
|----|-------------|--------|
| #52 | Deprecation notice for Lambda sync | 🔄 Open |

### terraform-modules

| Issue / PR | Description | Status |
|------------|-------------|--------|
| #225 | Move sync_flipsidecrypto_users_and_groups to SAM | 🔄 Open |
| #227 | Remove cloud operations from TerraformNullResource | 🔄 Open |
| #228 | Refactor library to focus on pipeline generation | 🔄 Open |
| #229 | Remove cloud data fetching methods | 🔄 Open |
| #226 | Cleanup PR (CLEANUP_PLAN.md) | 🔄 Open |

### cluster-ops (fsc-platform)

| PR | Description | Status |
|----|-------------|--------|
| #154 | Add vault-secret-sync deployment | 🔄 Open |

## Decision Required

Department heads need to select:
- [ ] **Option A**: SAM Approach (PR #44)
- [ ] **Option B**: vault-secret-sync (PR #43) - **Recommended**

## Key Insight

**Merging IS syncing** - if we sync to Vault KV2 "merge stores" instead of S3, vault-secret-sync handles both sync AND merge operations.

## Architecture Comparison

### Current (Fragmented)
```
terraform-aws-secretsmanager (Lambda sync)
terraform-modules (sync operations embedded)  
data-platform-secrets-syncing (SAM pipeline)
```

### Proposed (Unified with vault-secret-sync)
```
OpenBao → Audit Log → vault-secret-sync ┬→ AWS Secrets Manager
                                        └→ Also syncs to KV2 merge stores
```

## Next Steps After Decision

1. Merge selected proposal PR in data-platform-secrets-syncing
2. Merge cluster-ops PR #154 for deployment
3. Configure Vault audit log shipping
4. Validate sync operations
5. Execute terraform-modules cleanup (Issues #225-229)
6. Merge terraform-aws-secretsmanager PR #52 (deprecation)
7. Tear down old Lambda infrastructure

## Repository Links

- [data-platform-secrets-syncing](https://github.com/FlipsideCrypto/data-platform-secrets-syncing)
- [terraform-aws-secretsmanager](https://github.com/FlipsideCrypto/terraform-aws-secretsmanager)
- [terraform-modules](https://github.com/FlipsideCrypto/terraform-modules)
- [cluster-ops](https://github.com/fsc-platform/cluster-ops)
- [vault-secret-sync (upstream)](https://github.com/robertlestak/vault-secret-sync)
