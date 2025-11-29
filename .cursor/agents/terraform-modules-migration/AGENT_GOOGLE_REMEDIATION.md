# Agent Task: Google Operations Remediation

## Context
QC verification found significant discrepancies between terraform-modules and vendor-connectors Google operations.

## QC Findings Summary
Based on bc-f5391b3e-5208-4c16-94f8-ee24601f04be analysis:

1. **Workspace Operations Not 1:1**:
   - `get_google_users` in terraform_data_source.py has:
     - OU allow/deny filters
     - Active/bot user gating
     - Optional name flattening
     - Returns keyed dict by email
   - Current `list_users()` lacks these features

2. **Missing Filter/Shape Logic**:
   - User/group filtering by OU
   - Active status filtering
   - Bot account filtering
   - Name flattening utilities

3. **Cloud/IAM Orchestration Missing**:
   - Billing orchestration helpers not present
   - Service-specific inventory helpers absent

4. **Scope Limitations**:
   - GoogleConnector uses narrower OAuth scopes
   - Some operations may fail due to missing scopes

## Files to Modify

### `/workspace/packages/vendor-connectors/src/vendor_connectors/google/workspace.py`
Add optional filtering parameters to match terraform-modules:

```python
def list_users(
    self,
    customer: str = "my_customer",
    query: str | None = None,
    subject: str | None = None,
    unhump: bool = True,
    # NEW PARAMS:
    ou_allow_list: list[str] | None = None,  # Only include users in these OUs
    ou_deny_list: list[str] | None = None,   # Exclude users in these OUs
    include_suspended: bool = False,         # Include suspended users
    exclude_bots: bool = True,               # Exclude service accounts
    flatten_names: bool = False,             # Flatten name fields
    key_by_email: bool = False,              # Return dict keyed by email instead of list
) -> list[dict] | dict[str, dict]:
```

Similarly update `list_groups()`.

### `/workspace/packages/vendor-connectors/src/vendor_connectors/google/__init__.py`
Add missing scopes:
```python
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.orgunit",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloudplatformprojects",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/devstorage.full_control",
    "https://www.googleapis.com/auth/cloud-billing",
    "https://www.googleapis.com/auth/iam",  # ADD IF MISSING
    "https://www.googleapis.com/auth/sqlservice.admin",  # ADD IF MISSING
    "https://www.googleapis.com/auth/pubsub",  # ADD IF MISSING
]
```

## Source Reference
Clone terraform-modules to compare:
```bash
git clone https://oauth2:${GITHUB_JBCOM_TOKEN}@github.com/FlipsideCrypto/terraform-modules.git /tmp/terraform-modules
```

Key methods in `/tmp/terraform-modules/lib/terraform_modules/terraform_data_source.py`:
- `get_google_users` (~line 7789) - Has full filtering logic
- `get_google_groups` (~line 7924)
- `get_google_client_for_user` (~line 7914)

## Test Commands
```bash
cd /workspace && uv run python -m pytest packages/vendor-connectors/tests/test_google_connector.py -v --no-cov
uv run ruff check packages/vendor-connectors/src/vendor_connectors/google/
```

## Deliverables
1. Update `workspace.py` with optional filtering parameters
2. Update `__init__.py` with any missing scopes
3. Ensure backwards compatibility (new params are optional with defaults matching current behavior)
4. Tests pass
5. Lint passes
