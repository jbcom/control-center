locals {
  max_noncurrent_days         = var.config.max_noncurrent_days > 0 ? var.config.max_noncurrent_days : var.config.max_days
  noncurrent_transition_after = var.config.noncurrent_transition_after > 0 ? var.config.noncurrent_transition_after : var.config.transition_after

  enabled = var.config.enabled && (var.config.max_days > 0 || local.max_noncurrent_days > 0 || var.config.transition_after > 0 || local.noncurrent_transition_after > 0)
}

resource "aws_s3_bucket_lifecycle_configuration" "default" {
  count  = local.enabled ? 1 : 0
  bucket = var.bucket_name

  rule {
    id     = "default"
    status = "Enabled"

    filter {}

    dynamic "expiration" {
      for_each = var.config.max_days > 0 ? [var.config.max_days] : []
      content {
        days = expiration.value
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = local.max_noncurrent_days > 0 && var.config.max_noncurrent_versions > 0 ? [local.max_noncurrent_days] : []
      iterator = expiration
      content {
        newer_noncurrent_versions = var.config.max_noncurrent_versions
        noncurrent_days           = expiration.value
      }
    }

    dynamic "transition" {
      for_each = var.config.transition_after > 0 ? [var.config.transition_after] : []

      content {
        days          = var.config.transition_after
        storage_class = var.config.transition_to
      }
    }

    dynamic "noncurrent_version_transition" {
      for_each = local.max_noncurrent_days > 0 && var.config.max_noncurrent_versions > 0 && local.noncurrent_transition_after > 0 ? [local.noncurrent_transition_after] : []
      iterator = transition
      content {
        newer_noncurrent_versions = var.config.max_noncurrent_versions
        noncurrent_days           = transition.value
        storage_class             = coalesce(var.config.noncurrent_transition_to, var.config.transition_to)
      }
    }
  }
}
