/* Security Groups*/

resource "aws_security_group" "http" {
  name        = "http-${var.env}"
  description = "HTTP traffic"
  vpc_id      = aws_vpc.compass_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "https" {
  name        = "https-${var.env}"
  description = "HTTPS traffic"
  vpc_id      = aws_vpc.compass_vpc.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "egress_all" {
  name        = "egress-all-${var.env}"
  description = "Allow all outbound traffic"
  vpc_id      = aws_vpc.compass_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ingress_rpc" {
  name        = "ingress-rpc-${var.env}"
  description = "Allow ingress to RPC"
  vpc_id      = aws_vpc.compass_vpc.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "efs_mount" {
  name        = "efs-ecs-mount-${var.env}"
  description = "Allow all inbound from efs ecs target"
  vpc_id      = aws_vpc.compass_vpc.id

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.efs_mount_target.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "efs_mount_target" {
  name        = "efs-ecs-mount-target-${var.env}"
  description = "mount target"
  vpc_id      = aws_vpc.compass_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
