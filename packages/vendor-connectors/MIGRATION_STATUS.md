# Terraform Migration Status

| Function | Location | Status | Notes |
|----------|----------|--------|-------|
| `label_aws_account` | `vendor_connectors.aws.organizations` | ✅ Migrated | Provides AWS account labeling metadata used by terraform-modules.
| `classify_aws_accounts` | `vendor_connectors.aws.organizations` | ✅ Migrated | Builds classification-to-account maps compatible with prior terraform data source output.
| `preprocess_aws_organization` | `vendor_connectors.aws.organizations` | ✅ Migrated | Returns normalized org context (accounts, units, lookups) for terraform consumption.
| `build_github_actions_workflow` | `vendor_connectors.github` | ✅ Migrated | Generates GitHub Actions workflow YAML from python inputs.

All known terraform helper functions have now been ported. Future migrations should append to this table so FSC agents can audit parity at a glance.
