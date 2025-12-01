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
| <a name="input_allowlist"></a> [allowlist](#input\_allowlist) | n/a | `any` | `[]` | no |
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_config_dir"></a> [config\_dir](#input\_config\_dir) | n/a | `string` | `null` | no |
| <a name="input_config_dirs"></a> [config\_dirs](#input\_config\_dirs) | n/a | `any` | `[]` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_denylist"></a> [denylist](#input\_denylist) | n/a | `any` | `[]` | no |
| <a name="input_extra_record_categories"></a> [extra\_record\_categories](#input\_extra\_record\_categories) | n/a | `any` | `{}` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_merge_record"></a> [merge\_record](#input\_merge\_record) | n/a | `string` | `null` | no |
| <a name="input_merge_records"></a> [merge\_records](#input\_merge\_records) | n/a | `any` | `[]` | no |
| <a name="input_nest_config_under_key"></a> [nest\_config\_under\_key](#input\_nest\_config\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_nest_records_under_key"></a> [nest\_records\_under\_key](#input\_nest\_records\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_nest_sources_under_key"></a> [nest\_sources\_under\_key](#input\_nest\_sources\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_nest_state_under_key"></a> [nest\_state\_under\_key](#input\_nest\_state\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_ordered"></a> [ordered](#input\_ordered) | n/a | `any` | `null` | no |
| <a name="input_ordered_config_merge"></a> [ordered\_config\_merge](#input\_ordered\_config\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_parent_config_dirs_merge"></a> [ordered\_parent\_config\_dirs\_merge](#input\_ordered\_parent\_config\_dirs\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_parent_records_merge"></a> [ordered\_parent\_records\_merge](#input\_ordered\_parent\_records\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_parent_sources_merge"></a> [ordered\_parent\_sources\_merge](#input\_ordered\_parent\_sources\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_records_merge"></a> [ordered\_records\_merge](#input\_ordered\_records\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_sources_merge"></a> [ordered\_sources\_merge](#input\_ordered\_sources\_merge) | n/a | `bool` | `true` | no |
| <a name="input_ordered_state_merge"></a> [ordered\_state\_merge](#input\_ordered\_state\_merge) | n/a | `bool` | `true` | no |
| <a name="input_override_data"></a> [override\_data](#input\_override\_data) | n/a | `any` | `{}` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_parent_config_dirs"></a> [parent\_config\_dirs](#input\_parent\_config\_dirs) | n/a | `any` | `[]` | no |
| <a name="input_parent_records"></a> [parent\_records](#input\_parent\_records) | n/a | `any` | `[]` | no |
| <a name="input_passthrough_data_channel"></a> [passthrough\_data\_channel](#input\_passthrough\_data\_channel) | n/a | `any` | `null` | no |
| <a name="input_record_directories"></a> [record\_directories](#input\_record\_directories) | n/a | `any` | `{}` | no |
| <a name="input_source_data"></a> [source\_data](#input\_source\_data) | n/a | `any` | `[]` | no |
| <a name="input_source_directories"></a> [source\_directories](#input\_source\_directories) | n/a | `any` | `{}` | no |
| <a name="input_source_files"></a> [source\_files](#input\_source\_files) | n/a | `any` | `[]` | no |
| <a name="input_source_maps"></a> [source\_maps](#input\_source\_maps) | n/a | `any` | `[]` | no |
| <a name="input_state_key"></a> [state\_key](#input\_state\_key) | n/a | `string` | `"context"` | no |
| <a name="input_state_path"></a> [state\_path](#input\_state\_path) | n/a | `string` | n/a | yes |
| <a name="input_state_paths"></a> [state\_paths](#input\_state\_paths) | n/a | `any` | `{}` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_data"></a> [data](#output\_data) | Data query results |
