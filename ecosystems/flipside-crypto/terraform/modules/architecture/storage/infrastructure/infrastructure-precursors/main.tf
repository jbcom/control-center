locals {
  tags = var.context["tags"]

  precursor_data = {
    precursors = {
      datasync = {
        arns = {
          efs_filesystems = local.datasync_efs_role_arns
          s3_buckets      = local.datasync_s3_role_arns
        }

        names = {
          efs_filesystems = local.datasync_efs_role_names
          s3_buckets      = local.datasync_s3_role_names
        }
      }
    }
  }
}

module "permanent_record" {
  source = "../../../../utils/permanent-record"

  records = local.precursor_data

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}