# Workspace Generation Audit

**Generated**: 2025-11-29T05:05:07.539330

## Summary

- **Total Workspaces**: 44
- **With config.tf.json**: 44

### By Pipeline

| Pipeline | Workspaces |
|----------|------------|
| terraform-aws-organization | 37 |
| terraform-google-organization | 7 |

## Workspace Details


### terraform-aws-organization

- ✅ **aggregator**
  - State: `terraform/state/terraform-aws-organization/workspaces/aggregator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: False
- ✅ **authentication**
  - State: `terraform/state/terraform-aws-organization/workspaces/authentication/terraform.tfstate`
  - Providers: aws, github, google, googleworkspace, sops
  - Has main.tf: True
- ✅ **bots**
  - State: `terraform/state/terraform-aws-organization/workspaces/bots/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **components/compass/containers/compass/policies/rpc-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/policies/rpc-prod/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/policies/rpc-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/policies/rpc-stg/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/policies/workers-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/policies/workers-prod/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/policies/workers-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/policies/workers-stg/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/rpc-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/system-resources/rpc-prod/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/rpc-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/system-resources/rpc-stg/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/workers-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/system-resources/workers-prod/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/workers-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/system-resources/workers-stg/terraform.tfstate`
  - Providers: aws, awsutils, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/workers-stg/rpc**
  - State: `none`
  - Providers: aws, awsutils
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/workers-stg/rpc-stg**
  - State: `none`
  - Providers: aws, awsutils
  - Has main.tf: False
- ✅ **components/compass/containers/compass/system-resources/workers-stg/workers**
  - State: `none`
  - Providers: aws, awsutils
  - Has main.tf: False
- ✅ **components/compass/containers/compass/tasks/rpc-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/tasks/rpc-prod/terraform.tfstate`
  - Providers: aws, awsutils, cloudflare, github, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/tasks/rpc-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/tasks/rpc-stg/terraform.tfstate`
  - Providers: aws, awsutils, cloudflare, github, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/tasks/workers-prod**
  - State: `terraform/state/compass/workspaces/containers/compass/tasks/workers-prod/terraform.tfstate`
  - Providers: aws, awsutils, cloudflare, github, sops
  - Has main.tf: False
- ✅ **components/compass/containers/compass/tasks/workers-stg**
  - State: `terraform/state/compass/workspaces/containers/compass/tasks/workers-stg/terraform.tfstate`
  - Providers: aws, awsutils, cloudflare, github, sops
  - Has main.tf: False
- ✅ **components/compass/database-monitoring/prod**
  - State: `terraform/state/compass/workspaces/database-monitoring/prod/terraform.tfstate`
  - Providers: aws, sops
  - Has main.tf: False
- ✅ **components/compass/database-monitoring/stg**
  - State: `terraform/state/compass/workspaces/database-monitoring/stg/terraform.tfstate`
  - Providers: aws, sops
  - Has main.tf: False
- ✅ **components/compass/generator**
  - State: `terraform/state/compass/workspaces/generator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **components/compass/infrastructure**
  - State: `terraform/state/compass/workspaces/infrastructure/terraform.tfstate`
  - Providers: aws, cloudflare, datadog, sops
  - Has main.tf: True
- ✅ **components/compass/post-processing**
  - State: `terraform/state/compass/workspaces/post-processing/terraform.tfstate`
  - Providers: aws, cloudflare, sops
  - Has main.tf: True
- ✅ **components/datadog/generator**
  - State: `terraform/state/terraform-datadog-monitoring/workspaces/generator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: False
- ✅ **components/fireblocks/generator**
  - State: `terraform/state/terraform-treasury/workspaces/generator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: False
- ✅ **components/rstudio/generator**
  - State: `terraform/state/rstudio/workspaces/generator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: False
- ✅ **generator**
  - State: `terraform/state/terraform-aws-organization/workspaces/generator/terraform.tfstate`
  - Providers: aws, googleworkspace
  - Has main.tf: True
- ✅ **guards**
  - State: `terraform/state/terraform-aws-organization/workspaces/guards/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **organization**
  - State: `terraform/state/terraform-aws-organization/workspaces/organization/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **secrets**
  - State: `terraform/state/terraform-aws-organization/workspaces/secrets/terraform.tfstate`
  - Providers: aws, github
  - Has main.tf: True
- ✅ **security/aggregator**
  - State: `terraform/state/terraform-aws-security/workspaces/aggregator/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **security/config**
  - State: `terraform/state/terraform-aws-security/workspaces/config/terraform.tfstate`
  - Providers: aws
  - Has main.tf: False
- ✅ **security/delegation**
  - State: `terraform/state/terraform-aws-security/workspaces/delegation/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **security/guardduty**
  - State: `terraform/state/terraform-aws-security/workspaces/guardduty/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **security/macie**
  - State: `terraform/state/terraform-aws-security/workspaces/macie/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **security/securityhub**
  - State: `terraform/state/terraform-aws-security/workspaces/securityhub/terraform.tfstate`
  - Providers: aws
  - Has main.tf: True
- ✅ **sso**
  - State: `terraform/state/terraform-aws-organization/workspaces/sso/terraform.tfstate`
  - Providers: aws, googleworkspace
  - Has main.tf: True

### terraform-google-organization

- ✅ **gcp/authentication**
  - State: `terraform/state/terraform-google-organization/workspaces/gcp/authentication/terraform.tfstate`
  - Providers: aws, doppler, github, google, googleworkspace, postgresql, snowflake, sops
  - Has main.tf: True
- ✅ **gcp/functions**
  - State: `terraform/state/terraform-google-organization/workspaces/gcp/functions/terraform.tfstate`
  - Providers: aws, doppler, google, google-beta
  - Has main.tf: False
- ✅ **gcp/policies**
  - State: `terraform/state/terraform-google-organization/workspaces/gcp/policies/terraform.tfstate`
  - Providers: aws, doppler, google, google-beta
  - Has main.tf: True
- ✅ **gcp/projects**
  - State: `terraform/state/terraform-google-organization/workspaces/gcp/projects/terraform.tfstate`
  - Providers: aws, doppler, google, google-beta
  - Has main.tf: True
- ✅ **generator**
  - State: `terraform/state/terraform-google-organization/workspaces/generator/terraform.tfstate`
  - Providers: aws, google, google-beta, googleworkspace
  - Has main.tf: True
- ✅ **gws/assignments**
  - State: `terraform/state/terraform-google-organization/workspaces/gws/assignments/terraform.tfstate`
  - Providers: aws, doppler, googleworkspace
  - Has main.tf: True
- ✅ **gws/org_units**
  - State: `terraform/state/terraform-google-organization/workspaces/gws/org_units/terraform.tfstate`
  - Providers: aws, doppler, googleworkspace
  - Has main.tf: False
