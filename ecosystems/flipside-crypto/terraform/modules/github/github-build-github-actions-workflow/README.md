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
| <a name="input_concurrency_group"></a> [concurrency\_group](#input\_concurrency\_group) | n/a | `string` | `null` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_environment_variables"></a> [environment\_variables](#input\_environment\_variables) | n/a | `any` | `{}` | no |
| <a name="input_events"></a> [events](#input\_events) | n/a | `any` | `{}` | no |
| <a name="input_inputs"></a> [inputs](#input\_inputs) | n/a | `any` | `{}` | no |
| <a name="input_jobs"></a> [jobs](#input\_jobs) | n/a | `any` | n/a | yes |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_pull_requests"></a> [pull\_requests](#input\_pull\_requests) | n/a | `any` | `{}` | no |
| <a name="input_secrets"></a> [secrets](#input\_secrets) | n/a | `any` | `{}` | no |
| <a name="input_triggers"></a> [triggers](#input\_triggers) | n/a | `any` | `{}` | no |
| <a name="input_use_oidc_auth"></a> [use\_oidc\_auth](#input\_use\_oidc\_auth) | n/a | `bool` | `false` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |
| <a name="input_workflow_name"></a> [workflow\_name](#input\_workflow\_name) | n/a | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_workflow"></a> [workflow](#output\_workflow) | Data query results |
