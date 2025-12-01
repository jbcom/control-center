locals {
  state_path           = var.config.state_path != null ? var.config.state_path : var.state_path
  state_paths          = var.config.state_paths != null ? var.config.state_paths : var.state_paths
  state_key            = var.config.state_key != null ? var.config.state_key : var.state_key
  ordered_state_merge  = var.config.ordered_state_merge != null ? var.config.ordered_state_merge : var.ordered_state_merge
  nest_state_under_key = var.config.nest_state_under_key != null ? var.config.nest_state_under_key : var.nest_state_under_key

  merge_record            = var.config.merge_record != null ? var.config.merge_record : var.merge_record
  merge_records           = var.config.merge_records != null ? var.config.merge_records : var.merge_records
  record_directories      = var.config.record_directories != null ? var.config.record_directories : var.record_directories
  extra_record_categories = var.config.extra_record_categories != null ? var.config.extra_record_categories : var.extra_record_categories
  ordered_records_merge   = var.config.ordered_records_merge != null ? var.config.ordered_records_merge : var.ordered_records_merge
  nest_records_under_key  = var.config.nest_records_under_key != null ? var.config.nest_records_under_key : var.nest_records_under_key

  config_dir            = var.config.config_dir != null ? var.config.config_dir : var.config_dir
  config_dirs           = var.config.config_dirs != null ? var.config.config_dirs : var.config_dirs
  ordered_config_merge  = var.config.ordered_config_merge != null ? var.config.ordered_config_merge : var.ordered_config_merge
  nest_config_under_key = var.config.nest_config_under_key != null ? var.config.nest_config_under_key : var.nest_config_under_key

  nest_sources_under_key = var.config.nest_sources_under_key != null ? var.config.nest_sources_under_key : var.nest_sources_under_key
  ordered_sources_merge  = var.config.ordered_sources_merge != null ? var.config.ordered_sources_merge : var.ordered_sources_merge

  parent_records                   = var.config.parent_records != null ? var.config.parent_records : var.parent_records
  parent_config_dirs               = var.config.parent_config_dirs != null ? var.config.parent_config_dirs : var.parent_config_dirs
  ordered_parent_records_merge     = var.config.ordered_parent_records_merge != null ? var.config.ordered_parent_records_merge : var.ordered_parent_records_merge
  ordered_parent_config_dirs_merge = var.config.ordered_parent_config_dirs_merge != null ? var.config.ordered_parent_config_dirs_merge : var.ordered_parent_config_dirs_merge
  ordered_parent_sources_merge     = var.config.ordered_parent_sources_merge != null ? var.config.ordered_parent_sources_merge : var.ordered_parent_sources_merge

  allowlist = var.config.allowlist != null ? var.config.allowlist : var.allowlist
  denylist  = var.config.denylist != null ? var.config.denylist : var.denylist
}