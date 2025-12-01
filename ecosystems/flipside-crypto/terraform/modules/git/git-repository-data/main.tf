data "external" "query" {
  program = ["bash", "${path.module}/bin/query.sh"]
}

locals {
  result_data = data.external.query.result
}