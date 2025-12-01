
# VPC
data "aws_vpc" "vpc" {
  tags = {
    Name = var.vpc_name
  }
}

# Subnets
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }

  tags = {
    Tier = "private"
  }
}

data "aws_security_group" "efs_mount" {
  name = var.sg_efs_mount_name
}

resource "aws_efs_file_system" "efs" {
  encrypted = true

  tags = {
    Name = "${var.efs_name}-${var.env}"
    Env  = var.env
  }
}

resource "aws_efs_backup_policy" "policy" {
  file_system_id = aws_efs_file_system.efs.id

  backup_policy {
    status = "ENABLED"
  }
}

resource "aws_efs_mount_target" "mount_private_a" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = element(data.aws_subnets.private.ids, 0)
  security_groups = [
    data.aws_security_group.efs_mount.id
  ]
}

resource "aws_efs_mount_target" "mount_private_b" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = element(data.aws_subnets.private.ids, 1)
  security_groups = [
    data.aws_security_group.efs_mount.id
  ]
}

resource "aws_efs_mount_target" "mount_private_c" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = element(data.aws_subnets.private.ids, 2)
  security_groups = [
    data.aws_security_group.efs_mount.id
  ]
}

resource "aws_efs_mount_target" "mount_private_d" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = element(data.aws_subnets.private.ids, 3)
  security_groups = [
    data.aws_security_group.efs_mount.id
  ]
}

resource "aws_efs_mount_target" "mount_private_e" {
  file_system_id = aws_efs_file_system.efs.id
  subnet_id      = element(data.aws_subnets.private.ids, 4)
  security_groups = [
    data.aws_security_group.efs_mount.id
  ]
}
