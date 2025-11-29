# vendor-connectors API Reference

> **Version**: 202511.9.0  
> **Last Updated**: 2025-11-29

## Overview

`vendor-connectors` provides unified Python interfaces for cloud provider APIs. All connectors use the `DirectedInputsClass` pattern for consistent input handling.

---

## AWS Connector

### Base (`AWSConnector`)

| Method | Description | Status |
|--------|-------------|--------|
| `assume_role(role_arn, session_name)` | Assume IAM role | ✅ |
| `get_aws_session(role_arn?)` | Get boto3 session | ✅ |
| `get_aws_client(client_name, role_arn?)` | Get boto3 client | ✅ |
| `get_aws_resource(service_name, role_arn?)` | Get boto3 resource | ✅ |
| `get_caller_account_id()` | Get current account ID | ✅ |

### Secrets Manager (`AWSConnector`)

| Method | Description | Status |
|--------|-------------|--------|
| `get_secret(name, role_arn?)` | Get secret value | ✅ |
| `list_secrets(prefix?, get_values?, role_arn?)` | List secrets | ✅ |
| `create_secret(name, value, description?)` | Create secret | ✅ |
| `update_secret(name, value)` | Update secret | ✅ |
| `delete_secret(name, force?)` | Delete secret | ✅ |
| `delete_secrets_matching(prefix)` | Bulk delete by prefix | ✅ |
| `load_vendors_from_asm(prefix)` | Load vendor configs | ✅ |

### Organizations (`AWSOrganizationsMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `get_organization_accounts()` | List org accounts | ✅ | `get_aws_organization_accounts` |
| `get_controltower_accounts()` | List Control Tower accounts | ✅ | `get_aws_controltower_accounts` |
| `get_accounts()` | Combined org + CT accounts | ✅ | `get_aws_accounts` |
| `get_organization_units()` | List OUs | ✅ | - |
| `label_account()` | Tag an account | ❌ | `label_aws_account` |
| `classify_accounts()` | Classify by OU/tags | ❌ | `classify_aws_accounts` |
| `preprocess_organization()` | Terraform data prep | ❌ | `preprocess_aws_organization` |

### S3 (`AWSS3Mixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_s3_buckets()` | List buckets | ✅ | - |
| `get_bucket_location(bucket)` | Get bucket region | ✅ | - |
| `get_object(bucket, key)` | Get object | ✅ | - |
| `get_json_object(bucket, key)` | Get JSON object | ✅ | - |
| `put_object(bucket, key, body)` | Put object | ✅ | - |
| `put_json_object(bucket, key, data)` | Put JSON object | ✅ | - |
| `delete_object(bucket, key)` | Delete object | ✅ | - |
| `list_objects(bucket, prefix?)` | List objects | ✅ | - |
| `copy_object(src, dest)` | Copy object | ✅ | - |
| `get_bucket_features(bucket)` | Get bucket config | ✅ | `get_s3_bucket_features` |
| `find_buckets_by_name(contains)` | Find buckets | ✅ | `get_s3_buckets_containing_name` |
| `create_bucket(name, region?)` | Create bucket | ✅ | - |
| `delete_bucket(name, force?)` | Delete bucket | ✅ | - |
| `get_bucket_tags(bucket)` | Get tags | ✅ | - |
| `set_bucket_tags(bucket, tags)` | Set tags | ✅ | - |
| `get_bucket_sizes()` | Get sizes via CloudWatch | ✅ | `get_aws_s3_bucket_sizes_in_account` |

### SSO / Identity Center (`AWSSSOMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `get_identity_store_id()` | Get Identity Store ID | ✅ | `get_identity_store_id` |
| `get_sso_instance_arn()` | Get SSO instance ARN | ✅ | - |
| `list_sso_users()` | List SSO users | ✅ | `get_aws_users` |
| `get_sso_user(user_id)` | Get user details | ✅ | - |
| `create_sso_user(...)` | Create user | ✅ | - |
| `delete_sso_user(user_id)` | Delete user | ✅ | - |
| `list_sso_groups()` | List SSO groups | ✅ | `get_aws_groups` |
| `create_sso_group(...)` | Create group | ✅ | - |
| `delete_sso_group(group_id)` | Delete group | ✅ | - |
| `add_user_to_group(user, group)` | Add membership | ✅ | - |
| `remove_user_from_group(user, group)` | Remove membership | ✅ | - |
| `list_permission_sets()` | List permission sets | ✅ | `get_aws_sso_permission_sets` |
| `list_account_assignments()` | List assignments | ✅ | `get_aws_sso_account_assignments` |
| `create_account_assignment(...)` | Create assignment | ✅ | - |
| `delete_account_assignment(...)` | Delete assignment | ✅ | - |

### CodeDeploy (`AWSCodeDeployMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_applications()` | List apps | ✅ | - |
| `list_deployment_groups(app)` | List groups | ✅ | - |
| `list_deployments(app, group?)` | List deployments | ✅ | `get_aws_codedeploy_deployments` |
| `get_deployment(id)` | Get deployment | ✅ | - |
| `get_deployment_target(id, target)` | Get target | ✅ | - |
| `create_deployment(...)` | Create deployment | ✅ | - |
| `stop_deployment(id)` | Stop deployment | ✅ | - |

---

## Google Connector

### Base (`GoogleConnector`)

| Method | Description | Status |
|--------|-------------|--------|
| `credentials` | Get credentials | ✅ |
| `get_credentials_for_subject(email)` | Impersonation creds | ✅ |
| `get_connector_for_user(email)` | Impersonated connector | ✅ |
| `get_service(name, version)` | Get API service | ✅ |
| `list_users(...)` | List Workspace users | ✅ |
| `list_groups(...)` | List Workspace groups | ✅ |

### Workspace (`GoogleWorkspaceMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_users(...)` | List users with filtering | ✅ | `get_google_users` |
| `get_user(user_key)` | Get user | ✅ | - |
| `create_user(...)` | Create user | ✅ | - |
| `update_user(user_key, ...)` | Update user | ✅ | - |
| `delete_user(user_key)` | Delete user | ✅ | - |
| `list_groups(...)` | List groups with filtering | ✅ | `get_google_groups` |
| `get_group(group_key)` | Get group | ✅ | - |
| `create_group(...)` | Create group | ✅ | - |
| `delete_group(group_key)` | Delete group | ✅ | - |
| `list_group_members(group)` | List members | ✅ | - |
| `add_group_member(group, email)` | Add member | ✅ | - |
| `remove_group_member(group, member)` | Remove member | ✅ | - |
| `list_org_units()` | List OUs | ✅ | `get_google_org_units` |
| `create_or_update_user(...)` | Idempotent user | ✅ | - |
| `create_or_update_group(...)` | Idempotent group | ✅ | - |
| `list_available_licenses(customer_id)` | List licenses | ✅ | `list_available_google_workspace_licenses` |

### Cloud (`GoogleCloudMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `get_organization_id()` | Get org ID | ✅ | `get_google_organization_id` |
| `get_organization()` | Get org details | ✅ | - |
| `list_projects()` | List projects | ✅ | `get_google_projects` |
| `get_project(id)` | Get project | ✅ | - |
| `create_project(...)` | Create project | ✅ | - |
| `delete_project(id)` | Delete project | ✅ | - |
| `move_project(id, parent)` | Move project | ✅ | - |
| `list_folders()` | List folders | ✅ | - |
| `get_org_policy(resource, constraint)` | Get policy | ✅ | - |
| `set_org_policy(resource, constraint, ...)` | Set policy | ✅ | - |
| `get_iam_policy(resource)` | Get IAM | ✅ | - |
| `set_iam_policy(resource, policy)` | Set IAM | ✅ | - |
| `add_iam_binding(resource, role, member)` | Add binding | ✅ | - |
| `list_service_accounts(project)` | List SAs | ✅ | `get_service_accounts_for_google_project` |
| `create_service_account(...)` | Create SA | ✅ | - |

### Billing (`GoogleBillingMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_billing_accounts()` | List accounts | ✅ | `get_google_billing_accounts` |
| `get_billing_account(id)` | Get account | ✅ | `get_google_billing_account` |
| `get_project_billing_info(project)` | Get project billing | ✅ | `get_google_billing_account_for_project` |
| `update_project_billing_info(...)` | Link billing | ✅ | - |
| `disable_project_billing(project)` | Disable billing | ✅ | - |
| `list_billing_account_projects(account)` | List projects | ✅ | - |
| `get_billing_account_iam_policy(account)` | Get IAM | ✅ | - |
| `set_billing_account_iam_policy(...)` | Set IAM | ✅ | - |
| `get_bigquery_billing_dataset(project_id)` | Get billing export | ✅ | `get_google_bigquery_billing_dataset` |

### Services (`GoogleServicesMixin`)

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_compute_instances(project)` | List VMs | ✅ | `get_compute_instances_for_google_project` |
| `list_gke_clusters(project)` | List GKE | ✅ | `get_gke_clusters_for_google_project` |
| `get_gke_cluster(project, location, name)` | Get cluster | ✅ | - |
| `list_storage_buckets(project)` | List GCS buckets | ✅ | `get_storage_buckets_for_google_project` |
| `list_sql_instances(project)` | List Cloud SQL | ✅ | `get_sql_instances_for_google_project` |
| `list_pubsub_topics(project)` | List topics | ✅ | - |
| `list_pubsub_subscriptions(project)` | List subscriptions | ✅ | - |
| `list_enabled_services(project)` | List APIs | ✅ | `get_enabled_apis_for_google_project` |
| `enable_service(project, service)` | Enable API | ✅ | - |
| `disable_service(project, service)` | Disable API | ✅ | - |
| `batch_enable_services(project, services)` | Batch enable | ✅ | - |
| `list_kms_keyrings(project, location)` | List keyrings | ✅ | - |
| `create_kms_keyring(...)` | Create keyring | ✅ | - |
| `create_kms_key(...)` | Create key | ✅ | - |
| `is_project_empty(project)` | Check empty | ✅ | - |
| `get_project_iam_users(project_id)` | Get IAM users | ✅ | `get_users_for_google_project` |
| `get_pubsub_resources_for_project(project_id)` | Aggregate Pub/Sub | ✅ | `get_pubsub_queues_for_google_project` |
| `find_inactive_projects(...)` | Find dead projects | ✅ | `get_dead_google_projects` |

---

## GitHub Connector

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `get_repository_branch(name)` | Get branch | ✅ | - |
| `create_repository_branch(name)` | Create branch | ✅ | - |
| `get_repository_file(path)` | Get file | ✅ | - |
| `update_repository_file(path, data)` | Update file | ✅ | - |
| `delete_repository_file(path)` | Delete file | ✅ | - |
| `list_org_members(role?)` | List members | ✅ | `get_github_users` (partial) |
| `get_org_member(username)` | Get member | ✅ | - |
| `list_repositories(type?)` | List repos | ✅ | `get_github_repositories` |
| `get_repository(name)` | Get repo | ✅ | - |
| `list_teams(include_members?)` | List teams | ✅ | `get_github_teams` |
| `get_team(slug)` | Get team | ✅ | - |
| `add_team_member(team, user)` | Add member | ✅ | - |
| `remove_team_member(team, user)` | Remove member | ✅ | - |
| `execute_graphql(query)` | Run GraphQL | ✅ | - |
| `get_users_with_verified_emails(key_by_email?)` | Verified emails | ✅ | `get_github_users` (full) |
| `build_workflow(...)` | Build workflow YAML | ❌ | `build_github_actions_workflow` |

---

## Slack Connector

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `send_message(channel, text)` | Send message | ✅ | - |
| `get_bot_channels()` | Get bot channels | ✅ | - |
| `list_users(...)` | List users | ✅ | `get_slack_users` |
| `list_usergroups(...)` | List usergroups | ✅ | `get_slack_usergroups` |
| `list_conversations(...)` | List channels | ✅ | `get_slack_conversations` |

---

## Vault Connector

| Method | Description | Status | terraform-modules equivalent |
|--------|-------------|--------|------------------------------|
| `list_secrets(root_path, mount_point)` | List secrets | ✅ | - |
| `read_secret(path, mount_point)` | Read secret | ✅ | - |
| `get_secret(path, key?, mount_point?)` | Get secret value | ✅ | - |
| `write_secret(path, data, mount_point)` | Write secret | ✅ | - |
| `list_aws_iam_roles(prefix?)` | List AWS roles | ✅ | `get_vault_aws_iam_roles` |
| `get_aws_iam_role(role_name)` | Get role config | ✅ | - |
| `generate_aws_credentials(role)` | Generate creds | ✅ | - |

---

## Zoom Connector

| Method | Description | Status |
|--------|-------------|--------|
| `get_access_token()` | Get OAuth token | ✅ |
| `get_zoom_users()` | List users | ✅ |
| `create_zoom_user(...)` | Create user | ✅ |
| `remove_zoom_user(email)` | Remove user | ✅ |

---

## Migration Status Summary

| Area | Implemented | Remaining | Coverage |
|------|-------------|-----------|----------|
| AWS Organizations | 4 | 3 | 57% |
| AWS S3 | 15 | 0 | 100% |
| AWS SSO | 14 | 0 | 100% |
| AWS CodeDeploy | 7 | 0 | 100% |
| AWS Secrets | 7 | 0 | 100% |
| Google Workspace | 16 | 0 | 100% |
| Google Cloud | 14 | 0 | 100% |
| Google Billing | 9 | 0 | 100% |
| Google Services | 17 | 0 | 100% |
| GitHub | 15 | 1 | 94% |
| Slack | 5 | 0 | 100% |
| Vault | 7 | 0 | 100% |
| Zoom | 4 | 0 | 100% |
| **TOTAL** | **134** | **4** | **97%** |

### Remaining Functions to Migrate

1. **AWS Organizations**: `label_account`, `classify_accounts`, `preprocess_organization`
   - These are complex Terraform data preprocessing functions with FSC-specific logic
2. **GitHub**: `build_workflow`
   - Complex YAML workflow builder with many opinionated defaults

---

## Usage Example

```python
from vendor_connectors import VendorConnectors

# Initialize
vc = VendorConnectors()

# AWS
aws = vc.get_aws_connector(execution_role_arn="arn:aws:iam::123456789012:role/MyRole")
accounts = aws.get_accounts()

# Google
google = vc.get_google_client(service_account_file={"type": "service_account", ...})
users = google.list_users(exclude_bots=True, key_by_email=True)

# GitHub
github = vc.get_github_client(owner="myorg", token="ghp_...")
repos = github.list_repositories()
```
