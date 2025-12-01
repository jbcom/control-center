output "guardduty_detector" {
  value = aws_guardduty_detector.default.id

  description = "The GuardDuty detector"
}

output "guardduty_members" {
  value = aws_guardduty_member.member

  description = "Guardduty members data"
}