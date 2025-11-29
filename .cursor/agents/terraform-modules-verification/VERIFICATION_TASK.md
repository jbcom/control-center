# Terraform-Modules Migration Verification Task

## Objective
Verify that all Python code from `FlipsideCrypto/terraform-modules` has been successfully migrated 1:1 to `jbcom/jbcom-control-center` vendor-connectors package.

## Migration Target Repository
- **Source**: https://github.com/FlipsideCrypto/terraform-modules
- **Target**: https://github.com/jbcom/jbcom-control-center (packages/vendor-connectors)

## What Was Migrated

### AWS Operations (to `vendor_connectors.aws`)
- Organizations & Control Tower account management
- IAM Identity Center (SSO) operations
- S3 bucket & object operations
- Secrets Manager operations
- CodeDeploy deployments

### Google Operations (to `vendor_connectors.google`)
- Google Workspace Admin Directory (users, groups)
- Cloud Resource Manager (projects, folders)
- IAM roles and service accounts
- Billing account management
- Compute, Container (GKE), Storage, SQL Admin
- Pub/Sub, Service Usage, Cloud KMS

### GitHub Operations (to `vendor_connectors.github`)
- Organization members, repositories, teams
- GraphQL query support

### Other Connectors
- Slack (usergroups, conversations)
- Vault (AWS IAM role helpers)

## Verification Checklist

1. **Compare null_resource module Python code** with vendor-connectors implementations
2. **Compare terraform_data module Python code** with vendor-connectors implementations  
3. **Verify all helper functions** are present and functionally equivalent
4. **Check API coverage** - all AWS/Google/GitHub API calls should be in vendor-connectors
5. **Identify any gaps** - code in terraform-modules not yet migrated

## Key Files to Compare

### terraform-modules (source)
- `python/` directory
- `terraform_data/*/scripts/*.py`
- `null_resource/*/scripts/*.py`

### vendor-connectors (target)
- `packages/vendor-connectors/src/vendor_connectors/aws/`
- `packages/vendor-connectors/src/vendor_connectors/google/`
- `packages/vendor-connectors/src/vendor_connectors/github/`

## Report Format

Please create a verification report with:
1. **Coverage Summary** - percentage of code migrated
2. **Gap Analysis** - any functions/features NOT yet migrated
3. **Parity Confirmation** - confirm 1:1 functional equivalence
4. **Recommendations** - any additional work needed
