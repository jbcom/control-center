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
| <a name="input_allowed_extensions"></a> [allowed\_extensions](#input\_allowed\_extensions) | n/a | `any` | `[]` | no |
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_config"></a> [config](#input\_config) | n/a | `any` | `{}` | no |
| <a name="input_config_dir"></a> [config\_dir](#input\_config\_dir) | n/a | `string` | `null` | no |
| <a name="input_config_dirs"></a> [config\_dirs](#input\_config\_dirs) | n/a | `any` | `[]` | no |
| <a name="input_config_files_match"></a> [config\_files\_match](#input\_config\_files\_match) | n/a | `string` | `null` | no |
| <a name="input_config_glob"></a> [config\_glob](#input\_config\_glob) | n/a | `string` | `null` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_denied_extensions"></a> [denied\_extensions](#input\_denied\_extensions) | n/a | `any` | `[]` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_nest_config_under_key"></a> [nest\_config\_under\_key](#input\_nest\_config\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_ordered_config_merge"></a> [ordered\_config\_merge](#input\_ordered\_config\_merge) | n/a | `bool` | `true` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_config"></a> [config](#output\_config) | Data query results |
