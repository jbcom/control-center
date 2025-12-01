<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 3.47.0 |
| <a name="requirement_github"></a> [github](#requirement\_github) | 4.10.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 3.47.0 |
| <a name="provider_github"></a> [github](#provider\_github) | 4.10.0 |
| <a name="provider_local"></a> [local](#provider\_local) | n/a |
| <a name="provider_tls"></a> [tls](#provider\_tls) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_key_pair.default_keypair](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/key_pair) | resource |
| [github_actions_organization_secret.private_key](https://registry.terraform.io/providers/hashicorp/github/4.10.0/docs/resources/actions_organization_secret) | resource |
| [github_actions_organization_secret.public_key](https://registry.terraform.io/providers/hashicorp/github/4.10.0/docs/resources/actions_organization_secret) | resource |
| [github_user_ssh_key.public](https://registry.terraform.io/providers/hashicorp/github/4.10.0/docs/resources/user_ssh_key) | resource |
| [local_file.private](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file) | resource |
| [local_file.public](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file) | resource |
| [tls_private_key.ssh_key](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/resources/private_key) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_key_pair_name"></a> [key\_pair\_name](#input\_key\_pair\_name) | Key pair name | `string` | n/a | yes |
| <a name="input_write_key_pair_to_file"></a> [write\_key\_pair\_to\_file](#input\_write\_key\_pair\_to\_file) | Write the SSH key to a file | `bool` | `false` | no |
| <a name="input_write_key_pair_to_github"></a> [write\_key\_pair\_to\_github](#input\_write\_key\_pair\_to\_github) | Write the SSH key to Github Actions | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_key_pair_name"></a> [key\_pair\_name](#output\_key\_pair\_name) | n/a |
| <a name="output_key_pair_path"></a> [key\_pair\_path](#output\_key\_pair\_path) | n/a |
| <a name="output_ssh_key_id"></a> [ssh\_key\_id](#output\_ssh\_key\_id) | n/a |
| <a name="output_ssh_private_key"></a> [ssh\_private\_key](#output\_ssh\_private\_key) | n/a |
| <a name="output_ssh_public_key"></a> [ssh\_public\_key](#output\_ssh\_public\_key) | n/a |
<!-- END_TF_DOCS -->