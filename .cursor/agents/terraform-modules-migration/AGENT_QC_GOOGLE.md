# Agent Task: QC Verification - Google Operations

## Objective
Verify 1:1 accuracy of Google operations migrated from terraform-modules to vendor-connectors.

## Source Code Location
- Original: `/tmp/terraform-modules/lib/terraform_modules/terraform_data_source.py`
- Original (mutations): `/tmp/terraform-modules/lib/terraform_modules/terraform_null_resource.py`
- Migrated: `/workspace/packages/vendor-connectors/src/vendor_connectors/google/`

## Verification Checklist

### 1. Workspace Module (`google/workspace.py`)
Compare with source methods:
- `get_google_users` (~line 7789 in terraform_data_source.py)
- `get_google_groups` (~line 7924)
- `get_google_client_for_user` (~line 7914)
- `create_google_user` (~line 2915 in terraform_null_resource.py)
- `create_google_group` (~line 2968)

Verify:
- [ ] User pagination with nextPageToken
- [ ] Group member expansion logic
- [ ] Domain-wide delegation (subject impersonation)
- [ ] User creation with all fields
- [ ] Group creation and membership

### 2. Cloud Module (`google/cloud.py`)
Compare with source methods:
- `get_google_organization_id` (~line 5671)
- `get_google_projects` (~line 7128)
- `get_google_org_units` (~line 7593)
- `is_google_project_empty` (~line 6907)
- `create_google_project` (~line 1942 in terraform_null_resource.py)
- `delete_empty_google_project` (~line 2717)
- `assign_google_project_iam_roles` (~line 2100)
- `assign_service_account_to_google_organization` (~line 2174)
- `assign_service_account_to_google_project` (~line 2576)

Verify:
- [ ] Organization ID extraction from name
- [ ] Project listing with parent filtering
- [ ] OU recursive traversal
- [ ] Empty project detection logic
- [ ] IAM binding manipulation

### 3. Billing Module (`google/billing.py`)
Compare with source methods:
- `get_google_billing_accounts` (~line 5864)
- `get_google_billing_account` (~line 7261)
- `get_google_billing_account_for_project` (~line 5735)
- `link_google_billing_account` (~line 2661 in terraform_null_resource.py)
- `move_google_projects_to_billing_account` (~line 2804)

Verify:
- [ ] Billing account listing
- [ ] Project billing info retrieval
- [ ] Billing account linking

### 4. Services Module (`google/services.py`)
Compare with source methods:
- `get_storage_buckets_for_google_project` (~line 5921)
- `get_gke_clusters_for_google_project` (~line 5975)
- `get_compute_instances_for_google_project` (~line 6030)
- `get_service_accounts_for_google_project` (~line 6093)
- `get_sql_instances_for_google_project` (~line 6211)
- `get_pubsub_queues_for_google_project` (~line 6265)
- `get_enabled_apis_for_google_project` (~line 6348)
- `enable_google_apis` (~line 2033 in terraform_null_resource.py)
- `create_google_kms_key` (~line 1877)

Verify:
- [ ] Each service client creation
- [ ] Resource listing pagination
- [ ] API enablement batch operations
- [ ] KMS key creation

### 5. Base Connector (`google/__init__.py`)
Compare with source:
- `get_google_client` (~line 518)

Verify:
- [ ] Service account credential loading
- [ ] Service client caching
- [ ] Subject impersonation flow

## Test Commands
```bash
# Clone terraform-modules for comparison
git clone https://oauth2:${GITHUB_JBCOM_TOKEN}@github.com/FlipsideCrypto/terraform-modules.git /tmp/terraform-modules

# Run existing tests
cd /workspace && uv run python -m pytest packages/vendor-connectors/tests/test_google_connector.py -v

# Lint check
uv run ruff check packages/vendor-connectors/src/vendor_connectors/google/
```

## Reporting
Document any discrepancies found in a comment on this issue with:
1. Method name
2. Original behavior
3. Migrated behavior  
4. Fix required (if any)
