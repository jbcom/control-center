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
| <a name="input_aws_organization_units"></a> [aws\_organization\_units](#input\_aws\_organization\_units) | n/a | `any` | `null` | no |
| <a name="input_caller_account_id"></a> [caller\_account\_id](#input\_caller\_account\_id) | n/a | `string` | `null` | no |
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_domains"></a> [domains](#input\_domains) | n/a | `any` | `null` | no |
| <a name="input_label_aws_accounts"></a> [label\_aws\_accounts](#input\_label\_aws\_accounts) | n/a | `bool` | `false` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_sort_by_name"></a> [sort\_by\_name](#input\_sort\_by\_name) | n/a | `bool` | `false` | no |
| <a name="input_unhump_accounts"></a> [unhump\_accounts](#input\_unhump\_accounts) | n/a | `bool` | `true` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_accounts"></a> [accounts](#output\_accounts) | Data query results |
