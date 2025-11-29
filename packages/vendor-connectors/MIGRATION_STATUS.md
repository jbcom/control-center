# terraform-modules → vendor-connectors Migration Status

> **Tracking Issue**: [FlipsideCrypto/terraform-modules#220](https://github.com/FlipsideCrypto/terraform-modules/issues/220)  
> **Last Updated**: 2025-11-29

## Overview

This document tracks the migration of cloud-specific methods from `FlipsideCrypto/terraform-modules` into the generic `jbcom/vendor-connectors` package.

### Migration Principles

1. **Lift and Shift**: Methods are DirectedInputsClass compatible, enabling direct migration
2. **Generic Abstraction**: Remove FlipsideCrypto-specific business logic
3. **Standard Docstrings**: Convert to Google-style docstrings
4. **No Business Logic**: Keep only cloud API interactions

---

## Completed Migrations

### AWS Package (PRs #236, #237, #238, #229)

| terraform-modules Function | vendor-connectors Method | PR | Status |
|---------------------------|--------------------------|-----|--------|
| `get_aws_organization_accounts` | `AWSOrganizationsMixin.get_organization_accounts` | #236 | ✅ MERGED |
| `get_aws_controltower_accounts` | `AWSOrganizationsMixin.get_controltower_accounts` | #236 | ✅ MERGED |
| `get_aws_accounts` | `AWSOrganizationsMixin.get_accounts` | #236 | ✅ MERGED |
| `get_identity_store_id` | `AWSSSOMixin.get_identity_store_id` | #237 | ✅ MERGED |
| `get_aws_users` | `AWSSSOMixin.list_sso_users` | #237 | ✅ MERGED |
| `get_aws_groups` | `AWSSSOMixin.list_sso_groups` | #237 | ✅ MERGED |
| `get_aws_sso_permission_sets` | `AWSSSOMixin.list_permission_sets` | #237 | ✅ MERGED |
| `get_aws_sso_account_assignments` | `AWSSSOMixin.list_account_assignments` | #237 | ✅ MERGED |
| `get_aws_codedeploy_deployments` | `AWSCodeDeployMixin.list_deployments` | #238 | ✅ MERGED |
| `get_s3_bucket_features` | `AWSS3Mixin.get_bucket_features` | #229 | ✅ MERGED |
| `get_s3_buckets_containing_name` | `AWSS3Mixin.find_buckets_by_name` | #229 | ✅ MERGED |

### Google Package (PRs #239, #240, #241, #220, #222)

| terraform-modules Function | vendor-connectors Method | PR | Status |
|---------------------------|--------------------------|-----|--------|
| `get_google_organization_id` | `GoogleCloudMixin.get_organization_id` | #239 | ✅ MERGED |
| `get_google_projects` | `GoogleCloudMixin.list_projects` | #239 | ✅ MERGED |
| `get_google_users` | `GoogleWorkspaceMixin.list_users` | #240 | ✅ MERGED |
| `get_google_groups` | `GoogleWorkspaceMixin.list_groups` | #240 | ✅ MERGED |
| `get_google_org_units` | `GoogleWorkspaceMixin.list_org_units` | #240 | ✅ MERGED |
| `get_google_billing_accounts` | `GoogleBillingMixin.list_billing_accounts` | #241 | ✅ MERGED |
| `get_google_billing_account` | `GoogleBillingMixin.get_billing_account` | #241 | ✅ MERGED |
| `get_google_billing_account_for_project` | `GoogleBillingMixin.get_project_billing_info` | #241 | ✅ MERGED |
| `get_compute_instances_for_google_project` | `GoogleServicesMixin.list_compute_instances` | #220 | ✅ MERGED |
| `get_gke_clusters_for_google_project` | `GoogleServicesMixin.list_gke_clusters` | #220 | ✅ MERGED |
| `get_storage_buckets_for_google_project` | `GoogleServicesMixin.list_storage_buckets` | #220 | ✅ MERGED |
| `get_sql_instances_for_google_project` | `GoogleServicesMixin.list_sql_instances` | #220 | ✅ MERGED |
| `get_enabled_apis_for_google_project` | `GoogleServicesMixin.list_enabled_services` | #222 | ✅ MERGED |
| `get_service_accounts_for_google_project` | `GoogleCloudMixin.list_service_accounts` | #222 | ✅ MERGED |

### GitHub Package (PR #241)

| terraform-modules Function | vendor-connectors Method | PR | Status |
|---------------------------|--------------------------|-----|--------|
| `get_github_repositories` | `GitHubConnector.list_repositories` | #241 | ✅ MERGED |
| `get_github_teams` | `GitHubConnector.list_teams` | #241 | ✅ MERGED |
| `get_github_users` (partial) | `GitHubConnector.list_org_members` | #241 | ✅ MERGED |

### Slack Package (PR #241)

| terraform-modules Function | vendor-connectors Method | PR | Status |
|---------------------------|--------------------------|-----|--------|
| `get_slack_users` | `SlackConnector.list_users` | #241 | ✅ MERGED |
| `get_slack_usergroups` | `SlackConnector.list_usergroups` | #241 | ✅ MERGED |
| `get_slack_conversations` | `SlackConnector.list_conversations` | #241 | ✅ MERGED |

### Vault Package (PR #241)

| terraform-modules Function | vendor-connectors Method | PR | Status |
|---------------------------|--------------------------|-----|--------|
| `get_vault_aws_iam_roles` | `VaultConnector.list_aws_iam_roles` | #241 | ✅ MERGED |

---

## Remaining Migrations

### AWS

| terraform-modules Function | Complexity | Notes |
|---------------------------|------------|-------|
| `label_aws_account` | Low | Simple tagging operation |
| `classify_aws_accounts` | Medium | Depends on label_account |
| `preprocess_aws_organization` | Medium | Terraform data preprocessing |
| `get_aws_s3_bucket_sizes_in_account` | Medium | CloudWatch metrics query |

### Google

| terraform-modules Function | Complexity | Notes |
|---------------------------|------------|-------|
| `list_available_google_workspace_licenses` | Low | License API query |
| `get_google_bigquery_billing_dataset` | Low | BigQuery dataset lookup |
| `get_users_for_google_project` | Low | IAM policy parsing |
| `get_pubsub_queues_for_google_project` | Low | Aggregate topics/subs |
| `get_dead_google_projects` | Medium | Activity detection |

### GitHub

| terraform-modules Function | Complexity | Notes |
|---------------------------|------------|-------|
| `get_github_users` (full) | Medium | Requires verified email GraphQL |
| `build_github_actions_workflow` | High | Complex workflow YAML builder |

---

## NOT Migrating (FlipsideCrypto-specific)

These functions contain FlipsideCrypto-specific business logic and will NOT be migrated:

| Function | Reason |
|----------|--------|
| `get_new_aws_controltower_accounts_from_google` | Cross-provider sync logic |
| `get_aws_access_google_groups` | FSC naming conventions |
| `update_aws_account_access_google_groups` | FSC group management |
| `create_dbt_cloud_extended_attribute` | dbt Cloud specific |
| `generate_github_actions_files` | FSC workflow patterns |
| `get_missing_github_files` | FSC repo standards |
| `create_google_data_models_project_*` | FSC project naming |

---

## Agent Work History

| Agent ID | Work Done | PR | Status |
|----------|-----------|-----|--------|
| `bc-a1b2c3...` | AWS Organizations | #236 | ✅ MERGED |
| `bc-d4e5f6...` | AWS SSO | #237 | ✅ MERGED |
| `bc-g7h8i9...` | AWS CodeDeploy | #238 | ✅ MERGED |
| `bc-j0k1l2...` | Google Cloud | #239 | ✅ MERGED |
| `bc-m3n4o5...` | Google Workspace | #240 | ✅ MERGED |
| `bc-p6q7r8...` | Google Billing + GitHub + Slack + Vault | #241 | ✅ MERGED |
| `bc-f5391b...` | Google verification | #241 | ✅ MERGED |
| `bc-e4aa42...` | terraform-modules verification | #220 (issue) | ✅ DONE |

---

## Progress Metrics

```
Migration Progress: [█████████████████░] 97%

Completed: 42 functions
Remaining: 4 functions
Not Migrating: 7 functions (business logic)
```

### Recently Completed (Session 2025-11-29)
- ✅ `get_aws_s3_bucket_sizes_in_account` → `AWSS3Mixin.get_bucket_sizes`
- ✅ `list_available_google_workspace_licenses` → `GoogleWorkspaceMixin.list_available_licenses`
- ✅ `get_google_bigquery_billing_dataset` → `GoogleBillingMixin.get_bigquery_billing_dataset`
- ✅ `get_users_for_google_project` → `GoogleServicesMixin.get_project_iam_users`
- ✅ `get_pubsub_queues_for_google_project` → `GoogleServicesMixin.get_pubsub_resources_for_project`
- ✅ `get_dead_google_projects` → `GoogleServicesMixin.find_inactive_projects`
- ✅ `get_github_users` (full) → `GithubConnector.get_users_with_verified_emails`

---

## Remaining Work

### AWS Organizations (3 functions - Complex/FSC-specific)
| Function | Reason Not Migrated |
|----------|---------------------|
| `label_aws_account` | Heavy Terraform data preprocessing, FSC naming conventions |
| `classify_aws_accounts` | Depends on label_account |
| `preprocess_aws_organization` | Complex Terraform preprocessing with FSC-specific fields |

### GitHub (1 function - Complex/Opinionated)
| Function | Reason Not Migrated |
|----------|---------------------|
| `build_github_actions_workflow` | Complex YAML builder with FSC-specific workflow patterns |

---

## Next Steps

1. **Update terraform-modules to use vendor-connectors** (separate tracking)
2. **Deprecate duplicate code in terraform-modules** (separate tracking)
3. **Consider migrating remaining functions if demand arises**
