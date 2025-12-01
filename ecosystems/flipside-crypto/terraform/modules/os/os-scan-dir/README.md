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
| <a name="input_checksum"></a> [checksum](#input\_checksum) | Optional checksum to use for triggering resource updates | `string` | `""` | no |
| <a name="input_debug_markers"></a> [debug\_markers](#input\_debug\_markers) | Identifiers to generate verbose debug statements for | `list(string)` | `[]` | no |
| <a name="input_decode"></a> [decode](#input\_decode) | n/a | `bool` | `true` | no |
| <a name="input_denied_extensions"></a> [denied\_extensions](#input\_denied\_extensions) | n/a | `any` | `[]` | no |
| <a name="input_files_glob"></a> [files\_glob](#input\_files\_glob) | n/a | `string` | `"*"` | no |
| <a name="input_files_match"></a> [files\_match](#input\_files\_match) | n/a | `string` | `null` | no |
| <a name="input_files_path"></a> [files\_path](#input\_files\_path) | n/a | `string` | n/a | yes |
| <a name="input_flatten"></a> [flatten](#input\_flatten) | n/a | `bool` | `false` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Port library parameter | `string` | `"run.log"` | no |
| <a name="input_max_sanitize_depth"></a> [max\_sanitize\_depth](#input\_max\_sanitize\_depth) | n/a | `number` | `null` | no |
| <a name="input_params"></a> [params](#input\_params) | Override for multiple params | `any` | `{}` | no |
| <a name="input_paths_only"></a> [paths\_only](#input\_paths\_only) | n/a | `bool` | `false` | no |
| <a name="input_recursive"></a> [recursive](#input\_recursive) | n/a | `bool` | `true` | no |
| <a name="input_reject_dotfiles"></a> [reject\_dotfiles](#input\_reject\_dotfiles) | n/a | `bool` | `true` | no |
| <a name="input_replace_chars_in_key_using"></a> [replace\_chars\_in\_key\_using](#input\_replace\_chars\_in\_key\_using) | n/a | `any` | `null` | no |
| <a name="input_replace_chars_in_key_with"></a> [replace\_chars\_in\_key\_with](#input\_replace\_chars\_in\_key\_with) | n/a | `any` | `null` | no |
| <a name="input_repository_name"></a> [repository\_name](#input\_repository\_name) | n/a | `string` | `null` | no |
| <a name="input_repository_owner"></a> [repository\_owner](#input\_repository\_owner) | n/a | `string` | `null` | no |
| <a name="input_sanitize_keys"></a> [sanitize\_keys](#input\_sanitize\_keys) | n/a | `bool` | `false` | no |
| <a name="input_stem_only"></a> [stem\_only](#input\_stem\_only) | n/a | `bool` | `false` | no |
| <a name="input_verbose"></a> [verbose](#input\_verbose) | Port library parameter | `bool` | `false` | no |
| <a name="input_verbosity"></a> [verbosity](#input\_verbosity) | Port library parameter | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_tree"></a> [tree](#output\_tree) | Data query results |
