# Agent Task: Migrate Vault Operations to vendor-connectors

## Objective
Migrate Vault operations from `terraform-modules` to `vendor-connectors/vault/` package.

## Source Methods (from terraform_data_source.py)
- `get_vault_aws_iam_roles` (line ~8971) - List Vault AWS IAM roles for cross-account access

## Target Location
`/workspace/packages/vendor-connectors/src/vendor_connectors/vault/__init__.py`

## Migration Guidelines

### 1. Pattern to Follow
```python
def list_aws_iam_roles(
    self,
    mount_point: str = "aws",
    unhump_roles: bool = True,
) -> dict[str, dict[str, Any]]:
    """List AWS IAM roles configured in Vault.
    
    Args:
        mount_point: Vault mount point for AWS secrets engine.
        unhump_roles: Convert keys to snake_case. Defaults to True.
        
    Returns:
        Dictionary mapping role names to role configuration.
    """
```

### 2. Key Changes
- Remove `exit_run()` wrapper - return data directly
- Remove `exit_on_completion` parameter
- Add Google-style docstrings
- Use `unhump_map` from `extended_data_types` for snake_case conversion

### 3. Source Code Reference
```python
# From terraform_data_source.py ~line 8971
def get_vault_aws_iam_roles(self, exit_on_completion: bool = True):
    """Gets all vault AWS IAM roles for cross account access to AWS accounts
    generator=key: vault_aws_iam_roles, module_class: vault
    """
```

### 4. Existing Code Reference
Check `/workspace/packages/vendor-connectors/src/vendor_connectors/vault/__init__.py` for existing VaultConnector structure.

### 5. Methods to Add
1. `list_aws_iam_roles()` - List all AWS IAM roles in Vault
2. `get_aws_iam_role()` - Get specific role configuration
3. `create_aws_iam_role()` - Create new AWS IAM role
4. `delete_aws_iam_role()` - Delete AWS IAM role
5. `generate_aws_credentials()` - Generate temporary AWS credentials from role

### 6. Testing
Run: `uv run python -m pytest packages/vendor-connectors/tests -v --no-cov`

### 7. Completion Criteria
- [ ] All methods migrated with proper docstrings
- [ ] Linter passes: `uv run ruff check packages/vendor-connectors/src`
- [ ] Tests pass
- [ ] Create PR with changes
