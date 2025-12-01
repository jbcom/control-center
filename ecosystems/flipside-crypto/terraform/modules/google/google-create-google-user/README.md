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
| [env_sensitive.GOOGLE_SERVICE_ACCOUNT](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_exit_on_completion"></a> [exit\_on\_completion](#input\_exit\_on\_completion) | n/a | `bool` | `true` | no |
| <a name="input_family_name"></a> [family\_name](#input\_family\_name) | n/a | `string` | n/a | yes |
| <a name="input_given_name"></a> [given\_name](#input\_given\_name) | n/a | `string` | n/a | yes |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_primary_email"></a> [primary\_email](#input\_primary\_email) | n/a | `string` | n/a | yes |
| <a name="input_user_password"></a> [user\_password](#input\_user\_password) | n/a | `string` | n/a | yes |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

No outputs.
