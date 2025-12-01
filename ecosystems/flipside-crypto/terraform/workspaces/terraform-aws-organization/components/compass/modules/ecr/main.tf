resource "aws_ecr_repository" "ecr_rpc" {
  name                 = "${var.name}-rpc-${var.env}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name      = "${var.name}-rpc-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}

resource "aws_ecr_repository" "ecr_worker" {
  name                 = "${var.name}-worker-${var.env}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name      = "${var.name}-worker-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}
