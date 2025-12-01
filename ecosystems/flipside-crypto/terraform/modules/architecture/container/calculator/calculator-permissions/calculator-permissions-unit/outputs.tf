output "policy_document" {
  value = local.policy_document

  description = "Policy document"
}

output "policy_attachments" {
  value = local.policy_arns

  description = "Policy ARNs to attach"
}
