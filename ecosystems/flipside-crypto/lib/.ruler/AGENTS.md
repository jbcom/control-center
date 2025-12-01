# Python Library Agent Instructions

## Scope
This `.ruler/` applies to the `lib/terraform_modules/` Python library - the core engine that generates Terraform modules from Python functions.

## Architecture Overview

### Core Files
- `__main__.py` - CLI entry point (`tm_cli`), Lambda handler, method routing
- `terraform_data_source.py` - Data source functions (read-only operations)
- `terraform_null_resource.py` - Null resource functions (side-effect operations)
- `utils.py` - Base utilities, Doppler integration, output processing
- `terraform_module_resources.py` - Auto-generates Terraform modules from functions

### Client Files
- `aws_client.py` - AWS SDK wrapper with role assumption, caching
- `google_client.py` - Google Cloud and Workspace APIs
- `github_client.py` - GitHub API wrapper
- `vault_client.py` - HashiCorp Vault integration
- `slack_client.py` - Slack API wrapper
- `zoom_client.py` - Zoom API wrapper

### Support Files
- `settings.py` - Configuration and environment variable handling
- `errors.py` - Custom exception classes
- `logging.py` - Structured logging setup
- `doppler_config.py` - Doppler secrets integration
- `vault_config.py` - Vault authentication configuration

## Function Docstring Pattern (CRITICAL)

Every function that generates a Terraform module MUST have proper docstring annotations:

```python
def get_aws_accounts(self, **kwargs):
    """
    Retrieves AWS accounts from Organizations.
    
    module_class: aws
    description: Gets all AWS accounts in the organization
    
    Args:
        include_management: Include the management account
        filter_tags: Tags to filter accounts by
    
    Returns:
        List of AWS accounts with metadata
    
    Environment Variables:
        AWS_DEFAULT_REGION: AWS region (required)
        AWS_ROLE_ARN: Role to assume (optional)
    """
```

### Required Annotations
- `module_class:` - Provider category (aws, google, github, vault, utils, etc.)
- `description:` - Brief description for Terraform module README

### Optional Annotations
- `for_each: true` - Generate for_each module variant
- `sensitive_outputs:` - List of sensitive output fields
- `skip_module: true` - Don't generate Terraform module

## Adding New Functions

### Data Source Functions (Read Operations)
1. Add to `terraform_data_source.py`
2. Include proper docstring with `module_class:`
3. Return dictionary with results
4. Run `just terraform-modules` to generate

### Null Resource Functions (Side Effects)
1. Add to `terraform_null_resource.py`
2. Include proper docstring with `module_class:`
3. Use `self.ds` to access data source methods
4. Run `just terraform-modules` to generate

### Client Methods (Not Terraform Modules)
1. Add to appropriate `*_client.py`
2. These are internal APIs, not exposed as modules
3. Use `@cached` decorator for performance

## Testing Functions

```bash
# Test a single function
just tm get_aws_accounts --include_management true

# See all available functions
just show-methods

# Run pytest
just test
```

## Code Style

### Formatting
- Use `black` for formatting: `just fmt`
- Use `isort` for imports
- Maximum line length: 88 (black default)

### Type Hints
```python
def get_aws_accounts(
    self,
    include_management: bool = True,
    filter_tags: Optional[Dict[str, str]] = None,
    **kwargs
) -> Dict[str, Any]:
```

### Error Handling
```python
from lib.terraform_modules.errors import TerraformModulesError

try:
    result = client.operation()
except ClientError as e:
    raise TerraformModulesError(f"Operation failed: {e}")
```

## Environment Variables

### Core
- `DOPPLER_TOKEN` - Doppler secrets access
- `TM_VENDORS_SOURCE` - Where to load vendor secrets (`asm` or `doppler`)

### AWS
- `AWS_DEFAULT_REGION` - AWS region
- `AWS_ROLE_ARN` - Role to assume

### Google
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account JSON path
- `GOOGLE_SUBJECT` - Email to impersonate for Workspace APIs

### Vault
- `VAULT_ADDR` - Vault server address
- `VAULT_TOKEN` - Vault authentication token

## Common Patterns

### Caching Clients
```python
@cached(cache_key="aws_client_{role_arn}")
def get_aws_client(self, role_arn: str = None):
    # Client initialization
```

### Processing Terraform Inputs
```python
def my_function(self, **kwargs):
    # Get input with default
    value = kwargs.get("input_name", "default")
    
    # Boolean handling (Terraform passes strings)
    enabled = str(kwargs.get("enabled", "true")).lower() == "true"
```

### Returning Results
```python
# Always return a dictionary
return {
    "result": processed_data,
    "count": len(processed_data),
    "metadata": {"generated_at": datetime.now().isoformat()}
}
```

## Don't Do
- Don't add functions without `module_class:` annotation
- Don't forget to run `just terraform-modules` after changes
- Don't hardcode credentials - use Doppler/environment
- Don't use `print()` - use the logging module
- Don't commit test credentials or secrets
