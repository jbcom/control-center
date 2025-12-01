/* DB Subnets
*/
resource "aws_db_subnet_group" "public" {
  name = "${var.vpc_name}-${var.env}-db-subnet-group"
  subnet_ids = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id,
    aws_subnet.public_c.id,
    aws_subnet.public_d.id,
    aws_subnet.public_e.id
  ]

  tags = {
    Name = "${var.vpc_name}-${var.env}-db-subnet-group"
  }
}