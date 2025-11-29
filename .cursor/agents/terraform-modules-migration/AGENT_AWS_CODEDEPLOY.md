# Agent Task: Migrate AWS CodeDeploy Operations to vendor-connectors

## Objective
Create new `aws/codedeploy.py` module in vendor-connectors for CodeDeploy operations.

## Source Methods (from terraform-modules)
- `get_aws_codedeploy_deployments` (terraform_data_source.py ~line 4959) - List CodeDeploy deployments
- `create_codedeploy_deployment` (terraform_null_resource.py ~line 1448) - Create new deployment

## Target Location
Create new file: `/workspace/packages/vendor-connectors/src/vendor_connectors/aws/codedeploy.py`

## Migration Guidelines

### 1. Create Mixin Class
```python
"""AWS CodeDeploy operations.

This module provides operations for managing AWS CodeDeploy applications,
deployment groups, and deployments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from extended_data_types import unhump_map

if TYPE_CHECKING:
    pass


class AWSCodeDeployMixin:
    """Mixin providing AWS CodeDeploy operations.
    
    This mixin requires the base AWSConnector class to provide:
    - get_aws_client()
    - logger
    - execution_role_arn
    """
```

### 2. Methods to Implement
1. `list_applications()` - List CodeDeploy applications
2. `list_deployment_groups()` - List deployment groups for an application
3. `list_deployments()` - List deployments with filtering
4. `get_deployment()` - Get deployment details
5. `create_deployment()` - Create new deployment
6. `stop_deployment()` - Stop a running deployment

### 3. Update aws/__init__.py
Add import and include in `AWSConnectorFull`:
```python
from vendor_connectors.aws.codedeploy import AWSCodeDeployMixin

class AWSConnectorFull(AWSConnector, AWSOrganizationsMixin, AWSSSOixin, AWSS3Mixin, AWSCodeDeployMixin):
    pass
```

### 4. Testing
Run: `uv run python -m pytest packages/vendor-connectors/tests -v --no-cov`

### 5. Completion Criteria
- [ ] New codedeploy.py module created
- [ ] All methods implemented with proper docstrings
- [ ] Module exported in aws/__init__.py
- [ ] Linter passes: `uv run ruff check packages/vendor-connectors/src`
- [ ] Tests pass
- [ ] Create PR with changes
