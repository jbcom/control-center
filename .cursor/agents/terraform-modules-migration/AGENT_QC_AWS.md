# Agent Task: QC Verification - AWS Operations

## Objective
Verify 1:1 accuracy of AWS operations migrated from terraform-modules to vendor-connectors.

## Source Code Location
- Original: `/tmp/terraform-modules/lib/terraform_modules/terraform_data_source.py`
- Migrated: `/workspace/packages/vendor-connectors/src/vendor_connectors/aws/`

## Verification Checklist

### 1. Organizations Module (`aws/organizations.py`)
Compare with source methods:
- `get_aws_organization_accounts` (~line 4481)
- `get_aws_controltower_accounts` (~line 4576)
- `get_aws_accounts` (~line 4694)

Verify:
- [ ] All pagination logic preserved
- [ ] Tag retrieval matches original
- [ ] OU hierarchy traversal identical
- [ ] `unhump_accounts` transformation matches `unhump_map` behavior
- [ ] `managed` flag logic for Control Tower accounts

### 2. SSO Module (`aws/sso.py`)
Compare with source methods:
- `get_identity_store_id` (~line 593)
- `get_aws_users` (~line 3446)
- `get_aws_groups` (~line 3522)
- `get_aws_sso_permission_sets` (~line 3662)
- `get_aws_sso_account_assignments` (~line 3766)

Verify:
- [ ] Identity store ID retrieval correct
- [ ] User Name field flattening matches original
- [ ] Group membership expansion logic identical
- [ ] Permission set inline policy + managed policies fetched
- [ ] Account assignment pagination complete

### 3. S3 Module (`aws/s3.py`)
Compare with source methods:
- `get_s3_buckets_containing_name` (~line 3310)
- `get_s3_bucket_features` (~line 3363)

Verify:
- [ ] Bucket name matching logic
- [ ] Features extraction (logging, versioning, lifecycle, policy)
- [ ] Error handling for missing configurations

### 4. Base Connector (`aws/__init__.py`)
Compare with source methods:
- `get_aws_client` (~line 414)
- `get_aws_resource` (~line 441)
- `get_aws_session` (~line 468)
- `get_caller_account_id` (~line 583)

Verify:
- [ ] Session caching logic
- [ ] Role assumption flow
- [ ] Retry configuration

## Test Commands
```bash
# Clone terraform-modules for comparison
git clone https://oauth2:${GITHUB_JBCOM_TOKEN}@github.com//terraform-modules.git /tmp/terraform-modules

# Run existing tests
cd /workspace && uv run python -m pytest packages/vendor-connectors/tests/test_aws_connector.py -v

# Lint check
uv run ruff check packages/vendor-connectors/src/vendor_connectors/aws/
```

## Reporting
Document any discrepancies found in a comment on this issue with:
1. Method name
2. Original behavior
3. Migrated behavior
4. Fix required (if any)
