# Terragrunt Generate Blocks

## Overview

Terragrunt's `generate` blocks allow child configurations to create files (like `provider.tf` and `backend.tf`) dynamically. However, when using `include` to inherit from a parent configuration, duplicate generate block names can cause errors.

## Problem

When running `terragrunt run-all`, if both parent and child configurations define generate blocks with the same name, Terragrunt will fail with:

```
Error: Detected generate blocks with the same name: [provider backend]
```

## Solution

There are two approaches to avoid duplicate generate blocks:

### 1. Don't Include Parent Config (Used by Bootstrap)

If a child needs completely different settings, don't include the parent config at all:

```hcl
# DON'T include parent
# include "root" {
#   path = find_in_parent_folders()
# }

# Define your own generate blocks
generate "provider" {
  path = "provider.tf"
  # ... custom provider config
}
```

You can still read parent locals using `read_terragrunt_config()`:

```hcl
locals {
  root_config = read_terragrunt_config(find_in_parent_folders())
  repos = local.root_config.locals.all_repos
}
```

**Use when:** The child needs completely different provider/backend (like bootstrap using TFE instead of GitHub)

### 2. Use Unique Generate Block Names

If a child needs to override parent generate blocks, use unique names:

```hcl
include "root" {
  path = find_in_parent_folders()
}

# Use unique name to avoid collision
generate "bootstrap_provider" {
  path = "provider.tf"
  # ... will override parent's provider.tf
}
```

**Use when:** The child needs to override specific files while keeping other inherited settings

## Current Configuration

### Root (`terragrunt-stacks/terragrunt.hcl`)

Defines:
- `generate "provider"` - GitHub provider
- `generate "backend"` - Terraform Cloud backend

All repository stacks (python/*, nodejs/*, go/*, terraform/*) include this root config.

### Bootstrap (`terragrunt-stacks/bootstrap/terragrunt.hcl`)

Does NOT include root config. Defines:
- `generate "provider"` - TFE provider (different from root)
- `generate "backend"` - Bootstrap workspace (different from root)

Bootstrap reads root config via `read_terragrunt_config()` to access repo lists but doesn't inherit generate blocks.

### Other Stacks

- **strata** - Has `generate "imports"` (unique name, no conflict)
- All others - Use standard root generate blocks

## Validation

Run the validation script to check for duplicate generate block names:

```bash
./scripts/validate-terragrunt-generate-blocks.sh
```

This script:
1. Finds all `terragrunt.hcl` files
2. Checks if they include the root config
3. Compares generate block names with root
4. Reports any conflicts

The script runs automatically in CI as part of the terraform-sync workflow.

## Best Practices

1. **Default:** Include root config and use inherited generate blocks
2. **Override files:** Use unique generate block names (e.g., `mystack_provider`)
3. **Different providers:** Don't include root config, define your own
4. **Validate:** Run validation script before `terragrunt run-all`

## Troubleshooting

If you encounter the error:
```
Error: Detected generate blocks with the same name: [provider backend]
```

1. Run the validation script: `./scripts/validate-terragrunt-generate-blocks.sh`
2. Check which stacks have conflicting generate block names
3. Either remove the `include "root"` or rename the generate blocks to be unique
4. Verify with `terragrunt run-all plan --terragrunt-non-interactive`

## References

- [Terragrunt Generate Blocks Documentation](https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/#generate)
- [Terragrunt Include Documentation](https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/#include)
- [Terragrunt Troubleshooting Guide](https://terragrunt.gruntwork.io/docs/getting-started/troubleshooting/)
