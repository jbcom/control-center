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
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_denylist"></a> [denylist](#input\_denylist) | n/a | `any` | `[]` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_nest_records_under_key"></a> [nest\_records\_under\_key](#input\_nest\_records\_under\_key) | n/a | `string` | `null` | no |
| <a name="input_ordered_records_merge"></a> [ordered\_records\_merge](#input\_ordered\_records\_merge) | n/a | `bool` | `true` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_record_categories"></a> [record\_categories](#input\_record\_categories) | n/a | `any` | `{}` | no |
| <a name="input_record_directories"></a> [record\_directories](#input\_record\_directories) | n/a | `any` | `{}` | no |
| <a name="input_record_files"></a> [record\_files](#input\_record\_files) | n/a | `any` | `[]` | no |
| <a name="input_records"></a> [records](#input\_records) | n/a | `any` | `{}` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_records"></a> [records](#output\_records) | Data query results |
