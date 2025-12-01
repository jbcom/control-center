locals {
  canonical_user_ids = var.context["canonical_user_ids"]
}

data "aws_canonical_user_id" "current" {}

resource "aws_s3_bucket_acl" "unmanaged_grant_target" {
  for_each = {
    for bucket_id, bucket_data in data.aws_s3_bucket.unmanaged_s3_bucket : bucket_id => bucket_data if !local.s3_buckets_unmanaged_config[bucket_id]["skip_grants"]
  }

  bucket = each.value.id

  access_control_policy {
    dynamic "grant" {
      for_each = local.canonical_user_ids

      content {
        grantee {
          type = "CanonicalUser"
          id   = grant.value
        }

        permission = "FULL_CONTROL"
      }
    }

    dynamic "grant" {
      for_each = local.s3_buckets_unmanaged_config[each.key]["extra_grants"]

      content {
        grantee {
          type = grant.value["type"]
          id   = grant.key
        }

        permission = grant.value["permission"]
      }
    }

    owner {
      id = data.aws_canonical_user_id.current.id
    }
  }
}