# Active Context - FlipsideCrypto

## Current Focus: terraform-modules Library Cleanup

### PR #226: Library Cleanup
https://github.com/FlipsideCrypto/terraform-modules/pull/226

### Issues to Complete (in order)

| Issue | Description | Status |
|-------|-------------|--------|
| #225 | Move sync_flipsidecrypto_users_and_groups to SAM | **DO FIRST** |
| #229 | Remove cloud data methods (~35 methods) | After #225 |
| #227 | Remove cloud ops from TerraformNullResource | After #229 |
| #228 | Refactor to pipeline focus | Final |

### Goal
Reduce library from ~550KB to ~80KB, focused on pipeline generation only.

### Key Decisions
- Only `sync_flipsidecrypto_users_and_groups` goes to SAM (FSC-specific composite op)
- `sync_flipsidecrypto_rev_ops_groups` is legacy - DELETE
- All `get_aws_*`, `get_github_*`, etc. - DELETE (use vendor-connectors)
- All `create_*`, `delete_*` - DELETE (use vendor-connectors or Terraform)

### Dependencies
Library should use jbcom packages:
- `vendor-connectors` - Cloud operations
- `python-terraform-bridge` - Future: Terraform module generation

## How to Continue

```bash
# Clone terraform-modules
GH_TOKEN="$GITHUB_FSC_TOKEN" gh repo clone FlipsideCrypto/terraform-modules /tmp/terraform-modules

# Checkout cleanup branch
cd /tmp/terraform-modules
git checkout cleanup/remove-cloud-ops-use-vendor-connectors

# Work on issues in order
# See CLEANUP_PLAN.md for details
```

## Tooling

Use agentic-control CLI:
```bash
node packages/agentic-control/dist/cli.js fleet spawn \
  --repo FlipsideCrypto/terraform-modules \
  --task "Complete issue #225: Move sync to SAM"
```
