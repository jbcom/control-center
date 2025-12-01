locals {
  metadata = jsondecode(file("${path.module}/files/mongodb-atlas.json"))
}