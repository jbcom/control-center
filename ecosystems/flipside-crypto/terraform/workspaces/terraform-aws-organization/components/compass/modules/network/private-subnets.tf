/* Private Subnets
*/

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_a_private_cidr
  availability_zone = "us-east-1a"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | private | us-east-1a"
    "Tier" = "private"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_b_private_cidr
  availability_zone = "us-east-1b"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | private | us-east-1b"
    "Tier" = "private"
  }
}

resource "aws_subnet" "private_c" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_c_private_cidr
  availability_zone = "us-east-1c"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | private | us-east-1c"
    "Tier" = "private"
  }
}

resource "aws_subnet" "private_d" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_d_private_cidr
  availability_zone = "us-east-1d"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | private | us-east-1d"
    "Tier" = "private"
  }
}

resource "aws_subnet" "private_e" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_e_private_cidr
  availability_zone = "us-east-1e"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | private | us-east-1e"
    "Tier" = "private"
  }
}
