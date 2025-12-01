data "aws_caller_identity" "current" {}

# requires aws provider 3.48.0+
data "aws_iam_session_context" "current" {
  arn = data.aws_caller_identity.current.arn
}

# get the aws_caller_identity and aws_iam_session_context externally too, to compare them
data "external" "underlying-role-arn" {
  program = ["aws", "sts", "get-caller-identity"]
}

data "external" "aws_iam_session_context" {
  program = ["${path.module}/scripts/awsWithAssumeRole.sh", data.external.underlying-role-arn.result.Arn]
}