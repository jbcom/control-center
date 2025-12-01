## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.6 |
| <a name="requirement_env"></a> [env](#requirement\_env) | >=0.2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_env"></a> [env](#provider\_env) | >=0.2.0 |
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [terraform_data.default](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data) | resource |
| [env_var.EXECUTION_ROLE_ARN](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [env_var.ROLE_SESSION_NAME](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_execution_role_arn"></a> [execution\_role\_arn](#input\_execution\_role\_arn) | n/a | `string` | `null` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_role_session_name"></a> [role\_session\_name](#input\_role\_session\_name) | n/a | `string` | `null` | no |
| <a name="input_tag"></a> [tag](#input\_tag) | n/a | `string` | `null` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | n/a | `any` | `[]` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

No outputs.
