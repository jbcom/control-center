data "aws_iam_policy_document" "s3_read_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*"
    ]
    resources = [
      aws_s3_bucket.s3_bucket.arn,
      "${aws_s3_bucket.s3_bucket.arn}/*",
    ]
  }
}

resource "aws_iam_user" "sfuser" {
  name = "${var.env}_${var.name}_sfuser"
}

resource "aws_iam_user_policy" "sfuser_s3ropolicy" {
  name   = "sfuser_s3ropolicy"
  user   = aws_iam_user.sfuser.name
  policy = data.aws_iam_policy_document.s3_read_policy.json
}

resource "aws_iam_access_key" "sfuseraccesskey" {
  user = aws_iam_user.sfuser.name
}
