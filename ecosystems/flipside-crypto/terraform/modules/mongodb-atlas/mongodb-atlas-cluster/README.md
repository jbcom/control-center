<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_mongodbatlas"></a> [mongodbatlas](#requirement\_mongodbatlas) | 1.0.2 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |
| <a name="provider_mongodbatlas"></a> [mongodbatlas](#provider\_mongodbatlas) | 1.0.2 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_route.private_routes](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route) | resource |
| [aws_route.public_routes](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route) | resource |
| [aws_vpc_peering_connection_accepter.peer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_peering_connection_accepter) | resource |
| [mongodbatlas_network_peering.this](https://registry.terraform.io/providers/mongodb/mongodbatlas/1.0.2/docs/resources/network_peering) | resource |
| [mongodbatlas_project_ip_access_list.this](https://registry.terraform.io/providers/mongodb/mongodbatlas/1.0.2/docs/resources/project_ip_access_list) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [mongodbatlas_network_container.this](https://registry.terraform.io/providers/mongodb/mongodbatlas/1.0.2/docs/data-sources/network_container) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_container_id"></a> [container\_id](#input\_container\_id) | MongoDB Atlas Container ID | `string` | n/a | yes |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | MongoDB Atlas Project ID | `string` | n/a | yes |
| <a name="input_vpn_security_group_id"></a> [vpn\_security\_group\_id](#input\_vpn\_security\_group\_id) | Pritunl VPN security group ID | `string` | n/a | yes |
| <a name="input_vpn_vpc"></a> [vpn\_vpc](#input\_vpn\_vpc) | VPC data for the VPN VPC | `any` | n/a | yes |

## Outputs

No outputs.
<!-- END_TF_DOCS -->