## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.6 |
| <a name="requirement_env"></a> [env](#requirement\_env) | >=0.2.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >=2.3.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_external"></a> [external](#provider\_external) | >=2.3.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [external_external.default](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_defaults"></a> [defaults](#input\_defaults) | n/a | `any` | `{}` | no |
| <a name="input_local_module_source"></a> [local\_module\_source](#input\_local\_module\_source) | n/a | `any` | `null` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_map_name_to"></a> [map\_name\_to](#input\_map\_name\_to) | n/a | `any` | `{}` | no |
| <a name="input_map_sanitized_name_to"></a> [map\_sanitized\_name\_to](#input\_map\_sanitized\_name\_to) | n/a | `any` | `{}` | no |
| <a name="input_overrides"></a> [overrides](#input\_overrides) | n/a | `any` | `{}` | no |
| <a name="input_parameter_generators"></a> [parameter\_generators](#input\_parameter\_generators) | n/a | `any` | `{}` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_repository_name"></a> [repository\_name](#input\_repository\_name) | n/a | `any` | n/a | yes |
| <a name="input_repository_tag"></a> [repository\_tag](#input\_repository\_tag) | n/a | `any` | n/a | yes |
| <a name="input_requires_github_authentication"></a> [requires\_github\_authentication](#input\_requires\_github\_authentication) | n/a | `bool` | `false` | no |
| <a name="input_variable_files"></a> [variable\_files](#input\_variable\_files) | n/a | `any` | n/a | yes |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_variables"></a> [variables](#output\_variables) | Data query results |
