## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.6 |
| <a name="requirement_env"></a> [env](#requirement\_env) | >=0.2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_terraform"></a> [terraform](#provider\_terraform) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [terraform_data.default](https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_cleanup_records_dir"></a> [cleanup\_records\_dir](#input\_cleanup\_records\_dir) | n/a | `any` | `null` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_expand_records"></a> [expand\_records](#input\_expand\_records) | n/a | `bool` | `false` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_records"></a> [records](#input\_records) | n/a | `any` | n/a | yes |
| <a name="input_records_dir"></a> [records\_dir](#input\_records\_dir) | n/a | `string` | `"records"` | no |
| <a name="input_records_file_ext"></a> [records\_file\_ext](#input\_records\_file\_ext) | n/a | `string` | `".json"` | no |
| <a name="input_records_file_name"></a> [records\_file\_name](#input\_records\_file\_name) | n/a | `string` | `null` | no |
| <a name="input_save_empty_records"></a> [save\_empty\_records](#input\_save\_empty\_records) | n/a | `bool` | `false` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |
| <a name="input_workspace_dir"></a> [workspace\_dir](#input\_workspace\_dir) | n/a | `string` | `null` | no |

## Outputs

No outputs.
