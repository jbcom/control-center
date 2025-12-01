output "names" {
  value = formatlist("/compass/%s/%s", var.environment_name, keys(data.doppler_secrets.default.map))

  description = "Parameter names"
}