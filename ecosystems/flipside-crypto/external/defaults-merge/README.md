<!-- BEGIN_TF_DOCS -->
# Defaults-Merge

An issue (https://github.com/hashicorp/terraform/issues/18413) prevents using defaults to merge optional maps / lists
This serves as a replacement for that until the issue is resolved

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.0.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | >=2.2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_external"></a> [external](#provider\_external) | >=2.2.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [external_external.merge](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_defaults"></a> [defaults](#input\_defaults) | Defaults to merge into the source map.<br>If none are passed defaults are read from the 'defaults' sub-directory of this module. | `any` | `{}` | no |
| <a name="input_log_file_name"></a> [log\_file\_name](#input\_log\_file\_name) | Log file name for the merge. Defaults to MD5 hashes for the source map and defaults. | `string` | `""` | no |
| <a name="input_log_file_path"></a> [log\_file\_path](#input\_log\_file\_path) | Log file path for the merge. Defaults to logs/merges in the root module where executed. | `string` | `""` | no |
| <a name="input_source_map"></a> [source\_map](#input\_source\_map) | Source map to merge defaults into | `any` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_log_file"></a> [log\_file](#output\_log\_file) | Log file results were output to if logging was enabled |
| <a name="output_results"></a> [results](#output\_results) | Results of merging defaults into the source map |
<!-- END_TF_DOCS -->