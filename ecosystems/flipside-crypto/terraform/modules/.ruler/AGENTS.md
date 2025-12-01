# Terraform Orchestration Agent Instructions

## Scope
This `.ruler/` applies to the `terraform/` directory containing hand-written Terraform orchestration, particularly the `terraform-pipeline/` workflow generator.

## Architecture Overview

### terraform-pipeline
The main component generates complete Terraform workspace configurations including:
- Provider configurations with aliases
- Backend configurations
- Variable definitions
- Workspace-specific settings
- GitHub Actions workflow files

### Key Design Pattern: Enabled/Disabled Maps
```hcl
# Create maps with both enabled and disabled variants
local {
  vendor_config = {
    enabled  = { vendors_module_source = var.vendors_source }
    disabled = {}
  }
}

# Select based on condition
output "config" {
  value = local.vendor_config[var.use_vendors ? "enabled" : "disabled"]
}
```

## Directory Structure

```
terraform/
└── terraform-pipeline/
    ├── main.tf                 # Main module entry
    ├── variables.tf            # Input variables
    ├── outputs.tf              # Module outputs
    ├── versions.tf             # Provider requirements
    ├── workspaces.tf           # Workspace generation logic
    ├── workspaces_providers.tf # Provider configuration generation
    ├── defaults/               # Default configuration templates
    │   └── workspace/
    │       ├── providers.json  # Provider defaults
    │       └── ...
    └── templates/              # Template files
        └── workflow/
            └── steps.yaml.tpl  # GHA workflow steps
```

## Key Variables

### use_vendors
**Single source of truth** for vendor module loading:
```hcl
variable "use_vendors" {
  type        = bool
  default     = true
  description = "Enable vendor module loading (set false to completely disable)"
}
```

### Workspace Configuration
```hcl
variable "workspaces" {
  type = map(object({
    name          = string
    providers     = optional(map(any))
    variables     = optional(map(any))
    # ... other workspace settings
  }))
}
```

## Provider Configuration

### Default Provider with Alias
In `defaults/workspace/providers.json`:
```json
{
  "provider": {
    "github": {
      "alias": "FlipsideCrypto",
      "default": true,
      "owner": "FlipsideCrypto"
    }
  }
}
```

The `"default": true` flag creates BOTH:
1. An aliased provider (`github.FlipsideCrypto`)
2. A non-aliased default (`github`)

This supports gradual migration from non-aliased to aliased providers.

## Module Generation

The Python library generates provider configurations via:
```python
get_terraform_pipeline_providers_config()
```

This reduces ~300 lines of complex Terraform to ~11 lines by moving logic to Python.

## Common Patterns

### Conditional Resources
```hcl
resource "local_file" "config" {
  count    = var.enabled ? 1 : 0
  filename = "config.json"
  content  = jsonencode(local.config)
}
```

### Map Transformations
```hcl
locals {
  workspace_configs = {
    for name, workspace in var.workspaces : name => {
      providers = merge(local.default_providers, workspace.providers)
      variables = merge(local.default_variables, workspace.variables)
    }
  }
}
```

### Coalesce for Defaults
```hcl
locals {
  module_source = coalesce(
    var.custom_module_source,
    local.default_module_source
  )
}
```

## Testing

```bash
# Validate terraform-pipeline
just tf-validate terraform/terraform-pipeline

# Format all Terraform
just tf-fmt
```

## Code Style

### HCL Formatting
- Use `terraform fmt` (run via `just tf-fmt`)
- 2-space indentation
- Align `=` in blocks where readable

### Variable Naming
- Snake_case for variables and locals
- Descriptive names (no abbreviations)
- Boolean variables prefixed with `use_`, `enable_`, or `is_`

### Comments
```hcl
# Single line explanation

/*
Multi-line block for
complex explanations
*/
```

## Don't Do
- Don't add redundant control variables (use single `use_*` toggles)
- Don't modify generated outputs from terraform-pipeline manually
- Don't bypass the Python generator for provider logic
- Don't use deprecated `load_*` or `disable_*` variables (use `use_*`)

## MCP Tools for Terraform

Use these MCP servers when working on Terraform:
- **terraform** - HCL validation, module exploration, state ops
- **aws-documentation** - AWS resource documentation
- **context7** - Terraform provider documentation lookups

## Integration with Python Library

The `terraform-pipeline` module depends on the Python library for:
1. Provider configuration generation
2. Complex data transformations
3. Dynamic module discovery

When making changes that affect both:
1. Update Python code in `lib/terraform_modules/`
2. Run `just terraform-modules` 
3. Test with `just tf-validate terraform/terraform-pipeline`
