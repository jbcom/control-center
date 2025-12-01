<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.14.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 3.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 3.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_security_group.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group_rule.keyed](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_vpc.selected](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/vpc) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allow_all_egress"></a> [allow\_all\_egress](#input\_allow\_all\_egress) | A convenience that adds to the rules specified elsewhere a rule that allows all egress.<br>If this is false and no egress rules are specified via `rules` or `rule-matrix`, then no egress will be allowed. | `bool` | `false` | no |
| <a name="input_enabled"></a> [enabled](#input\_enabled) | Whether to enable the security group | `bool` | `true` | no |
| <a name="input_inline_rules_enabled"></a> [inline\_rules\_enabled](#input\_inline\_rules\_enabled) | NOT RECOMMENDED. Create rules "inline" instead of as separate `aws_security_group_rule` resources.<br>See [#20046](https://github.com/hashicorp/terraform-provider-aws/issues/20046) for one of several issues with inline rules.<br>See [this post](https://github.com/hashicorp/terraform-provider-aws/pull/9032#issuecomment-639545250) for details on the difference between inline rules and rule resources. | `bool` | `false` | no |
| <a name="input_revoke_rules_on_delete"></a> [revoke\_rules\_on\_delete](#input\_revoke\_rules\_on\_delete) | Instruct Terraform to revoke all of the Security Group's attached ingress and egress rules before deleting<br>the security group itself. This is normally not needed. | `bool` | `false` | no |
| <a name="input_rule_matrix"></a> [rule\_matrix](#input\_rule\_matrix) | A convenient way to apply the same set of rules to a set of subjects. See README for details. | `any` | `[]` | no |
| <a name="input_rules"></a> [rules](#input\_rules) | A list of Security Group rule objects. All elements of a list must be exactly the same type;<br>use `rules_map` if you want to supply multiple lists of different types.<br>The keys and values of the Security Group rule objects are fully compatible with the `aws_security_group_rule` resource,<br>except for `security_group_id` which will be ignored, and the optional "key" which, if provided, must be unique<br>and known at "plan" time.<br>To get more info see https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule . | `list(any)` | `[]` | no |
| <a name="input_rules_map"></a> [rules\_map](#input\_rules\_map) | A map-like object of lists of Security Group rule objects. All elements of a list must be exactly the same type,<br>so this input accepts an object with keys (attributes) whose values are lists so you can separate different<br>types into different lists and still pass them into one input. Keys must be known at "plan" time.<br>The keys and values of the Security Group rule objects are fully compatible with the `aws_security_group_rule` resource,<br>except for `security_group_id` which will be ignored, and the optional "key" which, if provided, must be unique<br>and known at "plan" time.<br>To get more info see https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule . | `any` | `{}` | no |
| <a name="input_security_group_create_timeout"></a> [security\_group\_create\_timeout](#input\_security\_group\_create\_timeout) | How long to wait for the security group to be created. | `string` | `"10m"` | no |
| <a name="input_security_group_delete_timeout"></a> [security\_group\_delete\_timeout](#input\_security\_group\_delete\_timeout) | How long to retry on `DependencyViolation` errors during security group deletion from<br>lingering ENIs left by certain AWS services such as Elastic Load Balancing. | `string` | `"15m"` | no |
| <a name="input_security_group_description"></a> [security\_group\_description](#input\_security\_group\_description) | The description to assign to the created Security Group.<br>Warning: Changing the description causes the security group to be replaced. | `string` | `"Managed by Terraform"` | no |
| <a name="input_security_group_name"></a> [security\_group\_name](#input\_security\_group\_name) | The name to assign to the security group. Must be unique within the VPC.<br>If `create_before_destroy` is true, will be used as a name prefix. | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | Resource tags | `map(string)` | `{}` | no |
| <a name="input_target_security_group_id"></a> [target\_security\_group\_id](#input\_target\_security\_group\_id) | The ID of an existing Security Group to which Security Group rules will be assigned.<br>The Security Group's description will not be changed.<br>Not compatible with `inline_rules_enabled` or `revoke_rules_on_delete`.<br>Required if `create_security_group` is `false`, ignored otherwise. | `list(string)` | `[]` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | The ID of the VPC where the Security Group will be created. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_arn"></a> [arn](#output\_arn) | The created Security Group ARN |
| <a name="output_id"></a> [id](#output\_id) | The created or target Security Group ID |
| <a name="output_name"></a> [name](#output\_name) | The created Security Group Name |
| <a name="output_rules_terraform_ids"></a> [rules\_terraform\_ids](#output\_rules\_terraform\_ids) | List of Terraform IDs of created `security_group_rule` resources, primarily provided to enable `depends_on` |
<!-- END_TF_DOCS -->