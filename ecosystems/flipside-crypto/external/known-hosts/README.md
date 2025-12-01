<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

No providers.

## Modules

No modules.

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_site"></a> [site](#input\_site) | Site to pull known-hosts for. Must match a file in .github/known-hosts | `string` | `"github"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_known_hosts"></a> [known\_hosts](#output\_known\_hosts) | GitHub known hosts |
<!-- END_TF_DOCS -->