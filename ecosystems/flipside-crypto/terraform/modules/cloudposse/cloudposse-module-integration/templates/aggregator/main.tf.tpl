module "infrastructure_metadata" {
  source = "$${REL_TO_ROOT}/terraform/modules/utils/permanent-record"

  records = var.infrastructure

  records_dir = format("%s/files", paths["metadata"])

  records_file_name = "infrastructure.json"
}

module "infrastructure_docs" {
  source = "$${REL_TO_ROOT}/terraform/modules/utils/permanent-record"

  records = var.docs

  records_dir = format("%s/files", paths["metadata"])

  records_file_name = "docs.json"
}
