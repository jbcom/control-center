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
| [env_sensitive.GOOGLE_SERVICE_ACCOUNT](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |
| [external_external.default](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_flatten_members"></a> [flatten\_members](#input\_flatten\_members) | n/a | `bool` | `false` | no |
| <a name="input_group_keys"></a> [group\_keys](#input\_group\_keys) | n/a | `any` | `[]` | no |
| <a name="input_group_names"></a> [group\_names](#input\_group\_names) | n/a | `any` | `null` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_members_only"></a> [members\_only](#input\_members\_only) | n/a | `bool` | `false` | no |
| <a name="input_only_status_for_members"></a> [only\_status\_for\_members](#input\_only\_status\_for\_members) | n/a | `string` | `null` | no |
| <a name="input_only_type_for_members"></a> [only\_type\_for\_members](#input\_only\_type\_for\_members) | n/a | `string` | `null` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_sort_by_name"></a> [sort\_by\_name](#input\_sort\_by\_name) | n/a | `bool` | `false` | no |
| <a name="input_unhump_groups"></a> [unhump\_groups](#input\_unhump\_groups) | n/a | `bool` | `true` | no |
| <a name="input_user_key"></a> [user\_key](#input\_user\_key) | n/a | `string` | `null` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_groups"></a> [groups](#output\_groups) | Data query results |
