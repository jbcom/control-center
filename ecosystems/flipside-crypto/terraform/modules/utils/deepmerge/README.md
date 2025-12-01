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
| <a name="input_nest_data_under_key"></a> [nest\_data\_under\_key](#input\_nest\_data\_under\_key) | n/a | `any` | `null` | no |
| <a name="input_ordered"></a> [ordered](#input\_ordered) | n/a | `bool` | `false` | no |
| <a name="input_override_data"></a> [override\_data](#input\_override\_data) | n/a | `any` | `{}` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_source_data"></a> [source\_data](#input\_source\_data) | n/a | `any` | `[]` | no |
| <a name="input_source_directories"></a> [source\_directories](#input\_source\_directories) | n/a | `any` | `{}` | no |
| <a name="input_source_files"></a> [source\_files](#input\_source\_files) | n/a | `any` | `[]` | no |
| <a name="input_source_maps"></a> [source\_maps](#input\_source\_maps) | n/a | `any` | `[]` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_merged_maps"></a> [merged\_maps](#output\_merged\_maps) | Data query results |
