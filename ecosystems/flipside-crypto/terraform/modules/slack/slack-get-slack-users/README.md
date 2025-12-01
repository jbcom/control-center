## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.6 |
| <a name="requirement_env"></a> [env](#requirement\_env) | >=0.2.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >=2.3.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_env"></a> [env](#provider\_env) | >=0.2.0 |
| <a name="provider_external"></a> [external](#provider\_external) | >=2.3.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [env_sensitive.SLACK_BOT_TOKEN](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |
| [env_sensitive.SLACK_TOKEN](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |
| [external_external.default](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_flatten_profile"></a> [flatten\_profile](#input\_flatten\_profile) | n/a | `bool` | `false` | no |
| <a name="input_flipsidecrypto_users_only"></a> [flipsidecrypto\_users\_only](#input\_flipsidecrypto\_users\_only) | n/a | `bool` | `false` | no |
| <a name="input_include_app_users"></a> [include\_app\_users](#input\_include\_app\_users) | n/a | `bool` | `false` | no |
| <a name="input_include_bots"></a> [include\_bots](#input\_include\_bots) | n/a | `bool` | `false` | no |
| <a name="input_include_deleted"></a> [include\_deleted](#input\_include\_deleted) | n/a | `bool` | `false` | no |
| <a name="input_include_locale"></a> [include\_locale](#input\_include\_locale) | n/a | `any` | `null` | no |
| <a name="input_limit"></a> [limit](#input\_limit) | n/a | `any` | `null` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_team_id"></a> [team\_id](#input\_team\_id) | n/a | `string` | `null` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_users"></a> [users](#output\_users) | Data query results |
