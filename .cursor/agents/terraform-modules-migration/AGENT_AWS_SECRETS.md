# Agent Task: Migrate AWS Secrets Manager Operations to vendor-connectors

## Objective
Extend `aws/__init__.py` with additional Secrets Manager operations from terraform-modules.

## Source Methods (from terraform-modules)
- `delete_matching_secrets_from_aws_accounts` (terraform_null_resource.py ~line 710) - Bulk delete secrets

## Target Location
`/workspace/packages/vendor-connectors/src/vendor_connectors/aws/__init__.py`

## Current State
The AWSConnector already has:
- `get_secret()` - Get single secret value
- `list_secrets()` - List secrets with filtering

## Methods to Add

### 1. delete_secret()
```python
def delete_secret(
    self,
    secret_id: str,
    force_delete: bool = False,
    recovery_window_days: int = 30,
    execution_role_arn: Optional[str] = None,
) -> dict[str, Any]:
    """Delete a secret from AWS Secrets Manager.
    
    Args:
        secret_id: The ARN or name of the secret.
        force_delete: Skip recovery window and delete immediately.
        recovery_window_days: Days before permanent deletion (7-30).
        execution_role_arn: ARN of role to assume.
        
    Returns:
        Delete secret response.
    """
```

### 2. create_secret()
```python
def create_secret(
    self,
    name: str,
    secret_value: str,
    description: str = "",
    tags: Optional[dict[str, str]] = None,
    execution_role_arn: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new secret in AWS Secrets Manager.
    
    Args:
        name: Name for the secret.
        secret_value: The secret value (string or JSON).
        description: Optional description.
        tags: Optional tags.
        execution_role_arn: ARN of role to assume.
        
    Returns:
        Create secret response with ARN.
    """
```

### 3. update_secret()
```python
def update_secret(
    self,
    secret_id: str,
    secret_value: str,
    execution_role_arn: Optional[str] = None,
) -> dict[str, Any]:
    """Update an existing secret value.
    
    Args:
        secret_id: The ARN or name of the secret.
        secret_value: The new secret value.
        execution_role_arn: ARN of role to assume.
        
    Returns:
        Update secret response.
    """
```

### 4. delete_secrets_matching()
```python
def delete_secrets_matching(
    self,
    name_prefix: str,
    force_delete: bool = False,
    dry_run: bool = True,
    execution_role_arn: Optional[str] = None,
) -> list[str]:
    """Delete all secrets matching a name prefix.
    
    Args:
        name_prefix: Prefix to match secret names.
        force_delete: Skip recovery window.
        dry_run: Only list secrets, don't delete.
        execution_role_arn: ARN of role to assume.
        
    Returns:
        List of deleted (or would-be-deleted) secret ARNs.
    """
```

## Testing
Run: `uv run python -m pytest packages/vendor-connectors/tests -v --no-cov`

## Completion Criteria
- [ ] All methods implemented with proper docstrings
- [ ] Linter passes: `uv run ruff check packages/vendor-connectors/src`
- [ ] Tests pass
- [ ] Create PR with changes
