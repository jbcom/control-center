locals {
  guardduty_config          = var.context["guardduty"]["configuration"]
  guardduty_member_accounts = var.context["guardduty_accounts"]["members"]
}

# GuardDuty Detector in the Delegated admin account
resource "aws_guardduty_detector" "default" {
  enable                       = true
  finding_publishing_frequency = var.gd_finding_publishing_frequency

  datasources {
    s3_logs {
      enable = true
    }

    kubernetes {
      audit_logs {
        enable = true
      }
    }

    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = var.context["tags"]
}

# Organization GuardDuty configuration in the Management account
resource "aws_guardduty_organization_admin_account" "default" {
  provider = aws.primary

  depends_on = [aws_guardduty_detector.default]

  admin_account_id = local.delegated_admin_account_id
}

# Organization GuardDuty configuration in the Delegated admin account
resource "aws_guardduty_organization_configuration" "default" {
  depends_on = [aws_guardduty_organization_admin_account.default]

  auto_enable = true
  detector_id = aws_guardduty_detector.default.id

  # Additional setting to turn on S3 Protection
  datasources {
    s3_logs {
      auto_enable = true
    }
  }
}

# GuardDuty members in the Delegated admin account
resource "aws_guardduty_member" "member" {
  depends_on = [aws_guardduty_organization_configuration.default]

  for_each = local.guardduty_member_accounts

  detector_id = aws_guardduty_detector.default.id
  invite      = true

  account_id                 = each.value["account_id"]
  disable_email_notification = true
  email                      = lookup(each.value, "email", format("%s@flipsidecrypto.com", each.key))

  lifecycle {
    ignore_changes = [
      email
    ]
  }
}

locals {
  guardduty_findings_data = var.context["guardduty_findings"]
}

# GuardDuty Publishing destination in the Delegated admin account
resource "aws_guardduty_publishing_destination" "default" {
  depends_on = [aws_guardduty_organization_admin_account.default]

  detector_id     = aws_guardduty_detector.default.id
  destination_arn = local.guardduty_findings_data["bucket_arn"]
  kms_key_arn     = local.guardduty_findings_data["kms_key_arn"]
}