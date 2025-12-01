<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >=4.0 |
| <a name="requirement_local"></a> [local](#requirement\_local) | >= 1.3 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >=4.0 |
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_state-storage-bucket"></a> [state-storage-bucket](#module\_state-storage-bucket) | git@github.com:FlipsideCrypto/terraform-aws-modules.git//modules/aws-s3-bucket | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_dynamodb_table.with_server_side_encryption](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table) | resource |
| [aws_iam_policy_document.prevent_unencrypted_uploads](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [terraform_remote_state.global](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/data-sources/remote_state) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_arn_format"></a> [arn\_format](#input\_arn\_format) | ARN format to be used. May be changed to support deployment in GovCloud/China regions. | `string` | `"arn:aws"` | no |
| <a name="input_billing_mode"></a> [billing\_mode](#input\_billing\_mode) | DynamoDB billing mode | `string` | `"PROVISIONED"` | no |
| <a name="input_enabled"></a> [enabled](#input\_enabled) | Whether to enable the state storage bucket | `bool` | `true` | no |
| <a name="input_kms_key_arn"></a> [kms\_key\_arn](#input\_kms\_key\_arn) | KMS key arn for the state storage bucket | `string` | n/a | yes |
| <a name="input_read_capacity"></a> [read\_capacity](#input\_read\_capacity) | DynamoDB read capacity units | `number` | `5` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags for the objects | `map(string)` | n/a | yes |
| <a name="input_team_name"></a> [team\_name](#input\_team\_name) | Team name | `string` | n/a | yes |
| <a name="input_write_capacity"></a> [write\_capacity](#input\_write\_capacity) | DynamoDB write capacity units | `number` | `5` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_config"></a> [config](#output\_config) | Team backend configuration |
| <a name="output_dynamodb_table"></a> [dynamodb\_table](#output\_dynamodb\_table) | Backend DynamoDB table data |
| <a name="output_s3_bucket"></a> [s3\_bucket](#output\_s3\_bucket) | S3 bucket data |
<!-- END_TF_DOCS -->