data "aws_caller_identity" "primary_account" {
  provider = aws.primary
}
