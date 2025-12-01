# GD Findings bucket KMS CMK policy
data "aws_iam_policy_document" "kms_pol" {

  statement {
    sid = "Allow use of the key for guardduty"
    actions = [
      "kms:GenerateDataKey*",
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:DescribeKey"
    ]

    resources = [
      "arn:aws:kms:${local.guardduty_config.default_region}:${local.guardduty_config.delegated_admin_acc_id}:key/*"
    ]

    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }
  }

  statement {
    sid = "Allow attachment of persistent resources for guardduty"
    actions = [
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant"
    ]

    resources = [
      "arn:aws:kms:${local.guardduty_config.default_region}:${local.guardduty_config.delegated_admin_acc_id}:key/*"
    ]

    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"

      values = [
        "true"
      ]
    }
  }

  statement {
    sid = "Allow all KMS Permissions for root account of GD Admin"
    actions = [
      "kms:*"
    ]

    resources = [
      "arn:aws:kms:${local.guardduty_config.default_region}:${local.guardduty_config.delegated_admin_acc_id}:key/*"
    ]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.guardduty_config.delegated_admin_acc_id}:root"]
    }
  }

  statement {
    sid = "Allow access for Key Administrators"
    actions = [
      "kms:Create*",
      "kms:Describe*",
      "kms:Enable*",
      "kms:List*",
      "kms:Put*",
      "kms:Update*",
      "kms:Revoke*",
      "kms:Disable*",
      "kms:Get*",
      "kms:Delete*",
      "kms:TagResource",
      "kms:UntagResource",
      "kms:ScheduleKeyDeletion",
      "kms:CancelKeyDeletion"
    ]

    resources = [
      "*"
    ]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.guardduty_config.delegated_admin_acc_id}:role/${var.assume_role_name}"]
    }
  }
}

# KMS CMK to be created to encrypt GD findings in the S3 bucket
resource "aws_kms_key" "gd_key" {
  provider                = aws.key
  description             = "GuardDuty findings encryption CMK"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_pol.json
  tags                    = var.context.tags
}

resource "aws_kms_alias" "kms_key_alias" {
  provider      = aws.key
  name          = "alias/${local.guardduty_config.security_acc_kms_key_alias}"
  target_key_id = aws_kms_key.gd_key.key_id
}