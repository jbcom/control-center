# Legacy SSO Diagnostics Scripts

These scripts have been replaced by the Go-based AWS SSO Manager tool located in `cmd/aws-sso-manager`.

The new tool provides the following advantages:
- Native HCL encoding for Terraform import statements
- Better error handling and logging
- More comprehensive validation and reporting
- Single binary distribution without dependencies on AWS CLI and jq

## Migration Guide

### Previous Usage:

```bash
# Generate import statements for a specific permission set
./sso_import_diagnostics.sh aws_ssoadmin_permission_set poweruseraccess

# Run diagnostics for multiple resources
./run_sso_diagnostics.sh
```

### New Usage:

```bash
# Generate import statements for all SSO resources
aws-sso-manager import --config-dir ./config --output ./workspaces/aws/organization/sso_imports.tf

# Validate configuration against AWS resources
aws-sso-manager validate --config-dir ./config

# Generate a detailed report
aws-sso-manager report --config-dir ./config --output ./reports/sso_report.md
```

See the main README in `cmd/aws-sso-manager` for more details on the new tool.
