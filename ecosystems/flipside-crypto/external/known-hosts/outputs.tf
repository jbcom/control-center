output "known_hosts" {
  value = chomp(file("${path.module}/files/${var.site}"))

  description = "Known hosts"
}