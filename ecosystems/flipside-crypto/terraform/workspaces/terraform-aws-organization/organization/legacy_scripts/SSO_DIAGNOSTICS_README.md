# SSO Import Diagnostics

This directory contains scripts to help diagnose and fix issues with SSO admin resources that have broken imports in Terraform.

## Scripts

### 1. sso_import_diagnostics.sh

This script helps diagnose issues with individual SSO admin resources that have broken imports.

#### Usage

```bash
./sso_import_diagnostics.sh [resource_type] [resource_name]
```

#### Examples

```bash
# Diagnose a permission set
./sso_import_diagnostics.sh aws_ssoadmin_permission_set poweruseraccess

# Diagnose an organization policy
./sso_import_diagnostics.sh aws_organizations_policy FullAWSAccess
```

#### Supported Resource Types

- `aws_ssoadmin_permission_set`: AWS SSO Permission Sets
- `aws_organizations_policy`: AWS Organizations Policies (Service Control Policies)

#### Features

- Lists all resources of the specified type
- Finds the resource by name
- Displays detailed information about the resource
- Generates Terraform import statements
- For permission sets, also generates import statements for account assignments

### 2. run_sso_diagnostics.sh

This script runs diagnostics for multiple SSO admin resources with broken imports.

#### Usage

```bash
./run_sso_diagnostics.sh
```

#### Configuration

Edit the `RESOURCES` array in the script to specify which resources to diagnose:

```bash
RESOURCES=(
  "aws_ssoadmin_permission_set:poweruseraccess"
  "aws_ssoadmin_permission_set:administratoraccess"
  "aws_ssoadmin_permission_set:viewonlyaccess"
  "aws_organizations_policy:FullAWSAccess"
)
```

## Prerequisites

- AWS CLI installed and configured
- jq installed (for JSON processing)
- AWS credentials with appropriate permissions to list and describe SSO resources and organization policies

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure the scripts are executable:
   ```bash
   chmod +x sso_import_diagnostics.sh run_sso_diagnostics.sh
   ```

2. **AWS CLI Not Installed**: Install the AWS CLI:
   ```bash
   pip install awscli
   ```

3. **jq Not Installed**: Install jq:
   ```bash
   # On macOS
   brew install jq
   
   # On Ubuntu/Debian
   apt-get install jq
   
   # On CentOS/RHEL
   yum install jq
   ```

4. **AWS Credentials Not Configured**: Configure AWS credentials:
   ```bash
   aws configure
   ```

5. **Insufficient Permissions**: Ensure your AWS credentials have the following permissions:
   - `sso-admin:ListInstances`
   - `sso-admin:ListPermissionSets`
   - `sso-admin:DescribePermissionSet`
   - `sso-admin:ListAccountAssignments`
   - `organizations:ListAccounts`
   - `organizations:ListPolicies`
   - `organizations:DescribePolicy`
   - `organizations:ListTargetsForPolicy`

## Using the Import Statements

The scripts generate Terraform import statements that you can use to import existing resources into your Terraform state. For example:

```bash
terraform import 'aws_ssoadmin_permission_set.this["poweruseraccess"]' arn:aws:sso:::instance/ssoins-1234567890abcdef,arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-1234567890abcdef
```

After running the import, you can use `terraform state show` to see the imported resource:

```bash
terraform state show 'aws_ssoadmin_permission_set.this["poweruseraccess"]'
```

This will help you create the correct Terraform configuration for the resource.
