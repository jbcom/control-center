module "sources_data" {
  source = "../utils-merge-sources"

  override_data = merge(var.context, {
    for k, v in module.this : k => v if k != "context"
    }, module.this.context, {
    tags = {
      for k, v in module.this.tags : k => v if k != "Name"
    }
  })

  state_path                       = local.state_path
  state_paths                      = local.state_paths
  state_key                        = local.state_key
  ordered_state_merge              = local.ordered_state_merge
  nest_state_under_key             = local.nest_state_under_key
  merge_record                     = local.merge_record
  merge_records                    = local.merge_records
  record_directories               = local.record_directories
  extra_record_categories          = local.extra_record_categories
  nest_records_under_key           = local.nest_records_under_key
  ordered_records_merge            = local.ordered_records_merge
  config_dir                       = local.config_dir
  config_dirs                      = local.config_dirs
  ordered_config_merge             = local.ordered_config_merge
  nest_config_under_key            = local.nest_config_under_key
  ordered_sources_merge            = local.ordered_sources_merge
  nest_sources_under_key           = local.nest_sources_under_key
  parent_records                   = local.parent_records
  ordered_parent_records_merge     = local.ordered_parent_records_merge
  parent_config_dirs               = local.parent_config_dirs
  ordered_parent_config_dirs_merge = local.ordered_parent_config_dirs_merge
  ordered_parent_sources_merge     = local.ordered_parent_sources_merge
  ordered                          = var.ordered
  allowlist                        = local.allowlist
  denylist                         = local.denylist
  passthrough_data_channel         = var.passthrough_data_channel

  log_file_name = "sources.log"
}
