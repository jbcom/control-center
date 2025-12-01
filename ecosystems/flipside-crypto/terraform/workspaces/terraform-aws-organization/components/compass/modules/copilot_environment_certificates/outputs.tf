output "arn" {
  value = aws_acm_certificate.cloudflare.arn

  description = "ACM Certificate ARN"
}