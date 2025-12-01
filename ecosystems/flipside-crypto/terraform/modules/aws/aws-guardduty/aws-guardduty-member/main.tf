locals {
  guardduty_detector        = var.context["guardduty_detector"]
  guardduty_member_accounts = var.context["guardduty_accounts"]["members"][var.unit_name]
}

resource "aws_guardduty_invite_accepter" "member" {
  detector_id       = local.guardduty_detector
  master_account_id = data.aws_caller_identity.primary_account.account_id
}

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