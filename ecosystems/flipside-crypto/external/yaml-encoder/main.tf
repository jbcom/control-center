data "external" "encoder" {
  program = ["python", "${path.module}/bin/encoder.py"]

  query = {
    data = jsonencode(var.data)
  }
}

locals {
  results_data = base64decode(data.external.encoder.result["yaml"])
}