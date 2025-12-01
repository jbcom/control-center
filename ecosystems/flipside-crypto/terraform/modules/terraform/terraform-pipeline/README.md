# terraform-pipeline

A comprehensive Terraform module for generating complete infrastructure pipeline configurations. This module processes workspace configurations and generates all necessary Terraform provider configurations, files, and workflows.

## Overview

The terraform-pipeline module has undergone a major architectural refactoring to move complex provider configuration logic from Terraform to Python, resulting in dramatically improved maintainability and support for complex nested configurations.

## Key Features

### Provider Configuration Processing
- **AWS Providers**: Multi-region support with automatic assume role configuration
- **Vendor Providers**: Support for complex nested parameters (e.g., Vault approle authentication)
- **Aliased Providers**: Merge base and alias configurations for multi-account setups
- **SOPS Integration**: Automatic encryption key management
- **Enable/Disable Logic**: Conditional provider activation based on workspace settings

### Architectural Improvements (v2.0)
- **Python-Powered Processing**: Moved 300+ lines of complex Terraform logic to a single comprehensive Python function
- **Nested Parameter Support**: Recursive processing of vendor parameters up to 3 levels deep
- **Type Safety**: Proper handling of mixed string/map configurations that caused Terraform type errors
- **Maintainability**: Easy to extend and debug in Python vs complex Terraform conditionals

## Usage

### Basic Usage

```hcl
module "terraform_pipeline" {
  source = "path/to/terraform-pipeline"

  # Required: Workspace configurations
  workspaces_config = {
    "my-workspace" = {
      providers                    = ["aws", "vault", "github"]
      aws_provider_regions        = ["us-east-1", "us-west-2"]
      backend_region             = "us-east-1"
      bind_to_account            = "arn:aws:iam::123456789012:role/TerraformRole"
      accounts = {
        "prod"    = "arn:aws:iam::123456789012:role/ProdRole"
        "staging" = "arn:aws:iam::987654321098:role/StagingRole"
      }
      provider_config = {
        vault = {
          parameters = {
            vendor = {
              auth_login = {
                path = "HCP_VAULT_APPROLE_ROLE_PATH"
                parameters = {
                  role_id    = "HCP_VAULT_APPROLE_ROLE_ID"
                  secret_id  = "HCP_VAULT_APPROLE_SECRET_ID"
                }
              }
            }
          }
        }
      }
    }
  }

  # Optional: SOPS configuration
  workspace_sops_config = {
    "my-workspace" = ["arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"]
  }
}
```

### Complex Nested Vendor Parameters

The module supports complex nested vendor configurations that were previously problematic:

```hcl
provider_config = {
  vault = {
    parameters = {
      vendor = {
        # Nested authentication configuration
        auth_login = {
          path = "HCP_VAULT_APPROLE_ROLE_PATH"
          parameters = {
            role_id    = "HCP_VAULT_APPROLE_ROLE_ID"
            secret_id  = "HCP_VAULT_APPROLE_SECRET_ID"
          }
        }
        # Static configuration mixed with vendor params
        static = {
          address = "https://vault.example.com:8200"
        }
      }
    }
  }
}
```

This gets automatically processed into proper Terraform provider configuration:

```hcl
provider "vault" {
  address = "https://vault.example.com:8200"
  auth_login {
    path = local.vendors_data.HCP_VAULT_APPROLE_ROLE_PATH
    parameters = {
      role_id   = local.vendors_data.HCP_VAULT_APPROLE_ROLE_ID
      secret_id = local.vendors_data.HCP_VAULT_APPROLE_SECRET_ID
    }
  }
}
```

### Provider Aliases

Support for aliased providers across multiple accounts:

```hcl
provider_config = {
  aws = {
    parameters = {
      aliases = {
        "prod" = {
          vendor = {
            "assume_role_arn" = "PROD_ASSUME_ROLE_ARN"
          }
        }
        "staging" = {
          vendor = {
            "assume_role_arn" = "STAGING_ASSUME_ROLE_ARN"
          }
        }
      }
    }
  }
}
```

## Architecture

### Provider Configuration Processing

The module uses a comprehensive Python function to handle all provider configuration logic:

```
terraform/terraform-pipeline/
├── workspaces_providers.tf     # Simple module call (11 lines)
└── ../terraform-get-terraform-pipeline-providers-config/
    ├── main.tf.json           # Generated Terraform module
    └── .library-module        # Python function reference
```

The Python function (`get_terraform_pipeline_providers_config`) in `lib/terraform_modules/data_sources/terraform.py`:

1. **Processes AWS providers** with regions, accounts, and assume roles
2. **Handles vendor parameters** with recursive nested support (max depth 3)
3. **Manages aliased providers** by merging base + alias configurations
4. **Configures SOPS providers** for encryption key management
5. **Implements enable/disable logic** based on workspace settings
6. **Generates required_providers** with proper version constraints

### Before vs After Architecture

**Before (Terraform-heavy):**
- 300+ lines of complex Terraform logic
- Nested for loops, conditionals, and transformations
- Type consistency issues with mixed string/map parameters
- Difficult to debug and maintain
- Error-prone conditional logic

**After (Python-powered):**
- 11 lines in Terraform (just module call)
- All complexity handled in Python
- Proper type handling and error messages
- Easy to extend and maintain
- Comprehensive processing in single function

## Outputs

The module provides the complete provider configuration:

- `providers_tf_json`: Complete Terraform provider and required_providers configuration
- `workspaces_files`: Generated workspace files and configurations
- `workflows`: GitHub Actions workflow configurations

## Dependencies

- **terraform_modules library**: Python functions for complex processing
- **External data source**: Bridge between Terraform and Python
- **SOPS**: For secret encryption/decryption
- **Git**: For workspace file management

## Development

### Adding New Provider Types

To add support for new provider types, update the Python function in `lib/terraform_modules/data_sources/terraform.py`:

```python
def get_terraform_pipeline_providers_config(self, ...):
    # Add new provider logic here
    new_provider_config = self.process_new_provider_type(...)
    
    # Include in final configuration
    providers_config["new_provider"] = new_provider_config
```

Then regenerate the Terraform module:

```bash
tm_cli terraform_modules
```

### Adding New Vendor Parameter Processing

The recursive vendor parameter processing can be extended by modifying the `process_vendor_params_recursive` function to handle new patterns.

## Migration from Legacy Version

If upgrading from the legacy Terraform-heavy version:

1. **No configuration changes required** - all workspace configurations remain the same
2. **Improved nested parameter support** - previously broken vault configurations now work
3. **Better error messages** - Python provides clearer error reporting
4. **Faster processing** - reduced Terraform complexity improves performance

## Troubleshooting

### Common Issues

**Nested vendor parameters not working:**
- Ensure you're using the latest version with Python-powered processing
- Check that nested parameters don't exceed 3 levels deep
- Verify vendor data keys exist in your environment

**Provider not found errors:**
- Check that the provider is listed in the workspace's `providers` array
- Verify provider configuration exists in `provider_config`
- Ensure required provider versions are available

**Module not found:**
- Run `terraform init` to install all required modules
- Verify the terraform-get-terraform-pipeline-providers-config module exists

### Debug Mode

Enable verbose logging in the Python function:

```hcl
module "terraform_pipeline" {
  # ... other config

  debug_markers = ["provider_processing", "vendor_params"]
  verbose      = true
  verbosity    = 2
}
```

## Contributing

1. **Provider logic changes**: Modify the Python function in `lib/terraform_modules/data_sources/terraform.py`
2. **Regenerate module**: Run `tm_cli terraform_modules` 
3. **Test changes**: Validate with `terraform validate` in a test workspace
4. **Update documentation**: Update this README with new features

## License

[Your license here]
