output "vpc_name" {
  value     = aws_vpc.compass_vpc.tags.Name
  sensitive = false
}

output "vpc_id" {
  value     = aws_vpc.compass_vpc.id
  sensitive = false
}

output "vpc_arn" {
  value     = aws_vpc.compass_vpc.arn
  sensitive = false
}

output "public_a_cidr_block" {
  value     = aws_subnet.public_a.cidr_block
  sensitive = false
}

output "public_b_cidr_block" {
  value     = aws_subnet.public_b.cidr_block
  sensitive = false
}

output "public_c_cidr_block" {
  value     = aws_subnet.public_c.cidr_block
  sensitive = false
}

output "public_d_cidr_block" {
  value     = aws_subnet.public_d.cidr_block
  sensitive = false
}

output "public_e_cidr_block" {
  value     = aws_subnet.public_e.cidr_block
  sensitive = false
}

output "public_a_id" {
  value     = aws_subnet.public_a.id
  sensitive = false
}

output "public_b_id" {
  value     = aws_subnet.public_b.id
  sensitive = false
}

output "public_c_id" {
  value     = aws_subnet.public_c.id
  sensitive = false
}

output "public_d_id" {
  value     = aws_subnet.public_d.id
  sensitive = false
}

output "public_e_id" {
  value     = aws_subnet.public_e.id
  sensitive = false
}

// private cidr blocks

output "private_a_cidr_block" {
  value     = aws_subnet.private_a.cidr_block
  sensitive = false
}

output "private_b_cidr_block" {
  value     = aws_subnet.private_b.cidr_block
  sensitive = false
}

output "private_c_cidr_block" {
  value     = aws_subnet.private_c.cidr_block
  sensitive = false
}

output "private_d_cidr_block" {
  value     = aws_subnet.private_d.cidr_block
  sensitive = false
}

output "private_e_cidr_block" {
  value     = aws_subnet.private_e.cidr_block
  sensitive = false
}

output "private_a_id" {
  value     = aws_subnet.private_a.id
  sensitive = false
}

output "private_b_id" {
  value     = aws_subnet.private_b.id
  sensitive = false
}

output "private_c_id" {
  value     = aws_subnet.private_c.id
  sensitive = false
}

output "private_d_id" {
  value     = aws_subnet.private_d.id
  sensitive = false
}

output "private_e_id" {
  value     = aws_subnet.private_e.id
  sensitive = false
}

// db subnet group
output "public_db_subnet_group_name" {
  value = aws_db_subnet_group.public.name
}


// sg
output "efs_mount_sg_id" {
  value = aws_security_group.efs_mount.id
}

output "efs_mount_target_sg_id" {
  value = aws_security_group.efs_mount_target.id
}

output "egress_all_sg_id" {
  value = aws_security_group.egress_all.id
}

output "ingress_rpc_sg_id" {
  value = aws_security_group.ingress_rpc.id
}

output "https_sg_id" {
  value = aws_security_group.https.id
}

output "http_sg_id" {
  value = aws_security_group.http.id
}

// Security Group Names

output "sg_http_name" {
  value = aws_security_group.http.name
}

output "sg_https_name" {
  value = aws_security_group.https.name
}

output "sg_egress_all_name" {
  value = aws_security_group.egress_all.name
}

output "sg_ingress_rpc_name" {
  value = aws_security_group.ingress_rpc.name
}

output "sg_efs_mount_target_name" {
  value = aws_security_group.efs_mount_target.name
}

output "sg_efs_mount_name" {
  value = aws_security_group.efs_mount.name
}
