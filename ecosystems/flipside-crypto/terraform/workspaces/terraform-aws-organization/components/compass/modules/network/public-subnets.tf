/* Public Subnets
*/

resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_a_public_cidr
  availability_zone = "us-east-1a"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | public | us-east-1a"
    "Tier" = "public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_b_public_cidr
  availability_zone = "us-east-1b"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | public | us-east-1b"
    "Tier" = "public"
  }
}

resource "aws_subnet" "public_c" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_c_public_cidr
  availability_zone = "us-east-1c"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | public | us-east-1c"
    "Tier" = "public"
  }
}

resource "aws_subnet" "public_d" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_d_public_cidr
  availability_zone = "us-east-1d"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | public | us-east-1d"
    "Tier" = "public"
  }
}

resource "aws_subnet" "public_e" {
  vpc_id            = aws_vpc.compass_vpc.id
  cidr_block        = var.subnet_e_public_cidr
  availability_zone = "us-east-1e"

  tags = {
    "Name" = "${var.vpc_name}-${var.env} | public | us-east-1e"
    "Tier" = "public"
  }
}
