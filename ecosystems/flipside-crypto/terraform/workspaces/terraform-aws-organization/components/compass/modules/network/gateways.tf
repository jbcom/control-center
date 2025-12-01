
resource "aws_eip" "nat" {
  vpc = true
  tags = {
    Name = "${var.vpc_name}-${var.env}-nat"
    Env  = var.env
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.compass_vpc.id
  tags = {
    Name = "${var.vpc_name}-${var.env}-igw"
    Env  = var.env
  }
}

resource "aws_nat_gateway" "ngw" {
  subnet_id     = aws_subnet.public_d.id
  allocation_id = aws_eip.nat.id
  tags = {
    Name = "${var.vpc_name}-${var.env}-ngw"
    Env  = var.env
  }

  depends_on = [aws_internet_gateway.igw]
}

resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route" "private_ngw" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.ngw.id
}
