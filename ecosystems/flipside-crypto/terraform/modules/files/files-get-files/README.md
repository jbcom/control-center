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
| [env_sensitive.ACTIONS_ID_TOKEN_REQUEST_TOKEN](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |
| [env_sensitive.GITHUB_TOKEN](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/sensitive) | data source |
| [env_var.ACTIONS_ID_TOKEN_REQUEST_URL](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [env_var.GITHUB_ACTIONS](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [env_var.GITHUB_BRANCH](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [env_var.GITHUB_OWNER](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [env_var.GITHUB_REPO](https://registry.terraform.io/providers/tcarreira/env/latest/docs/data-sources/var) | data source |
| [external_external.default](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allowed_extensions"></a> [allowed\_extensions](#input\_allowed\_extensions) | n/a | `any` | `[]` | no |
| <a name="input_charset"></a> [charset](#input\_charset) | n/a | `string` | `"utf-8"` | no |
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_decode"></a> [decode](#input\_decode) | n/a | `bool` | `true` | no |
| <a name="input_denied_extensions"></a> [denied\_extensions](#input\_denied\_extensions) | n/a | `any` | `[]` | no |
| <a name="input_errors"></a> [errors](#input\_errors) | n/a | `string` | `"strict"` | no |
| <a name="input_files"></a> [files](#input\_files) | n/a | `any` | `[]` | no |
| <a name="input_gitignore_file"></a> [gitignore\_file](#input\_gitignore\_file) | n/a | `string` | `null` | no |
| <a name="input_headers"></a> [headers](#input\_headers) | n/a | `any` | `{}` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_match_dotfiles"></a> [match\_dotfiles](#input\_match\_dotfiles) | n/a | `bool` | `false` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_relative_to_root"></a> [relative\_to\_root](#input\_relative\_to\_root) | n/a | `string` | `null` | no |
| <a name="input_repository_name"></a> [repository\_name](#input\_repository\_name) | n/a | `string` | `null` | no |
| <a name="input_repository_owner"></a> [repository\_owner](#input\_repository\_owner) | n/a | `string` | `null` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_files"></a> [files](#output\_files) | Data query results |
