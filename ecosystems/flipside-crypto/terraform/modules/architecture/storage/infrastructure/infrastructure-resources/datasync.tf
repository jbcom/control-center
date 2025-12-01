locals {
  datasync_private_data = {
    s3_buckets = {
      for bucket_name, sync_data in module.datasync-s3-managed-private : coalesce(local.configured_s3_buckets_private_only[bucket_name]["bucket_id"], bucket_name) => sync_data
    }

    efs_filesystems = {
      for fs_name, sync_data in module.datasync-efs-managed-private : coalesce(local.configured_efs_filesystems_private_only[fs_name]["id"], fs_name) => sync_data
    }
  }

  datasync_public_data = {
    s3_buckets = {
      for bucket_name, sync_data in module.datasync-s3-managed-public : coalesce(local.configured_s3_buckets_public_only[bucket_name]["bucket_id"], bucket_name) => sync_data
    }

    efs_filesystems = {
      for fs_name, sync_data in module.datasync-efs-managed-public : coalesce(local.configured_efs_filesystems_public_only[fs_name]["id"], fs_name) => sync_data
    }
  }
}