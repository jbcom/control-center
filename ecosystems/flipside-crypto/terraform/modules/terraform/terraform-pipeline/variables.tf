variable "workflow" {
  type = object({
    workflow_name     = string
    concurrency_group = optional(string)

    enable = optional(bool, true)

    use_oidc_auth = optional(bool, true)

    # Use HTTPS with FLIPSIDE_GITHUB_TOKEN instead of SSH key for git operations
    # This is useful for cross-org pipelines where SSH keys can't be synced (PRIVATE visibility)
    use_https_git_auth = optional(bool, false)

    environment_variables = optional(map(string), {})

    release = optional(object({
      publish  = optional(bool, false)
      prefix   = optional(string, "v")
      branch   = optional(string, "main")
      job_name = optional(string, "publish")
    }), {})

    events = optional(object({
      push         = optional(bool, true)
      pull_request = optional(bool, true)
      release      = optional(bool, false)
      schedule     = optional(list(string), [])
      call         = optional(bool, true)
      dispatch     = optional(bool, true)
    }), {})

    triggers = optional(object({
      files       = optional(list(string), [])
      directories = optional(list(string), [])
      paths       = optional(list(string), [])
      branches    = optional(list(string), [])
      tags        = optional(list(string), [])
    }), {})

    inputs = optional(map(object({
      default     = optional(any)
      required    = bool
      type        = string
      description = optional(string)
      key         = optional(string)
    })), {})

    allow_build_and_push_only = optional(bool, false)

    pull_requests = optional(object({
      ignored_branches = optional(list(string), [])
      ignored_paths    = optional(list(string), [])
      merge_queue      = optional(bool, false)
    }), {})

    autopopulate = optional(object({
      paths    = optional(bool, false)
      branches = optional(bool, true)
    }), {})

    call = optional(object({
      before = optional(list(string), [])
      after  = optional(list(string), [])
    }), {})

    dispatch = optional(list(object({
      organization = optional(string, "FlipsideCrypto")
      repository   = string
      branch       = optional(string, "main")
      workflow     = optional(string, "generator.yml")
      job_name     = optional(string)
    })), [])

    secrets     = optional(map(string), {})
    secret_keys = optional(list(string), [])

    python_lockfile = optional(string, ".github/Pipfile.lock")
  })

  description = "Workflow configuration for a Terraform pipeline"
}

variable "workspaces" {
  type = map(object({
    workspace_name   = optional(string)
    workspace_branch = optional(string, "main")

    conditions = optional(any, {})

    managed = optional(bool, true)

    job_name = optional(string)

    root_dir               = string
    workspaces_in_root_dir = optional(bool, false)
    workspace_dir          = optional(string, "workspaces")
    workspace_dir_name     = optional(string)

    validate_workspace = optional(bool, true)

    dependencies            = optional(list(string), [])
    terragrunt_dependencies = optional(list(string), [])
    extra_terragrunt_hcl    = optional(string)

    docker_images = optional(any, {})

    run_before_docker = optional(string)
    run_after_docker  = optional(string)

    disable_backend                   = optional(bool, false)
    backend_workspace_name            = optional(string)
    backend_bucket_name               = string
    backend_bucket_workspaces_path    = string
    backend_dynamodb_table            = string
    backend_region                    = optional(string, "us-east-1")
    terraform_version                 = string
    python_version                    = string
    install_terraform_modules_library = optional(bool, true)

    use_vendors = optional(bool, true)

    default_module_source = optional(string, "git@github.com:FlipsideCrypto/terraform-modules.git/")
    context_module_source = optional(string)
    context_module_path   = optional(string, "utils/context")

    disable_config = optional(bool, false)

    accounts        = optional(map(string), {})
    bind_to_account = optional(string, "")

    local_files      = optional(map(string), {})
    local_json_files = optional(map(string), {})
    local_yaml_files = optional(map(string), {})

    config_files_dir  = optional(string, "files")
    extra_json_config = optional(any, {})
    extra_yaml_config = optional(any, {})

    disable_context = optional(bool, false)

    bind_to_context = optional(object({
      object_key = optional(string)

      name            = optional(string)
      tenant          = optional(string)
      environment     = optional(string)
      stage           = optional(string, "$${local.region}")
      namespace       = optional(string)
      attributes      = optional(list(string))
      tags            = optional(map(string))
      label_order     = optional(list(string))
      label_key_case  = optional(string, "title")
      id_length_limit = optional(number)

      state_path  = optional(string)
      state_paths = optional(map(string))
      state_key   = optional(string, "context")

      merge_record       = optional(string)
      merge_records      = optional(list(string), [])
      record_directories = optional(map(string), {})
      records_base_path  = optional(string)
      extra_record_paths = optional(list(string))
      extra_record_categories = optional(map(object({
        records_path = string
        pattern      = optional(string, "*.json")
      })))
      nest_records_under_key = optional(string)

      config_dir               = optional(string)
      nest_config_under_key    = optional(string)
      config_dirs              = optional(list(string), [])
      config_key_replace_chars = optional(string)
      config_key_delimiter     = optional(string)

      rel_to_root = optional(string)

      ordered_state_merge   = optional(bool)
      ordered_records_merge = optional(bool)
      ordered_config_merge  = optional(bool)

      nest_sources_under_key = optional(string)
      ordered_sources_merge  = optional(bool)

      allowlist = optional(list(string))
      denylist  = optional(list(string))

      debug         = optional(bool)
      verbose_debug = optional(bool)
    }), {})

    parent_context = optional(object({
      parent_records                   = optional(list(string), [])
      parent_config_dirs               = optional(list(string), [])
      ordered_parent_records_merge     = optional(bool)
      ordered_parent_config_dirs_merge = optional(bool)
      ordered_parent_sources_merge     = optional(bool)
    }), {})

    install_additional_python_requirements = optional(bool, false)

    environment_variables = optional(map(string), {})

    runner_label = optional(string, "ubuntu-latest")

    run_before_apply = optional(string)
    run_after_apply  = optional(string)

    providers = optional(list(string), [])

    provider_overrides = optional(map(object({
      source  = string
      version = string
    })), {})

    disable_providers                   = optional(bool, false)
    disable_providers_requiring_secrets = optional(bool, false)

    aws_provider_ignore_tags = optional(object({
      keys         = optional(list(string), [])
      key_prefixes = optional(list(string), [])
    }), {})

    aws_provider_regions = optional(list(string), [])

    provider_version_constraint = optional(string, "<=")

    secrets_kms_key_arn = optional(string, "")

    secrets_kms_key = optional(any, {})

    extra_files = optional(map(string), {})

    vendor_secrets_dir    = optional(string, "")
    workspace_secrets_dir = optional(string, "secrets")

    docs_sections_pre = optional(list(object({
      title       = string
      description = optional(string)

      snippets = optional(list(object({
        title   = string
        content = string
      })), [])

      tables = optional(list(object({
        title       = string
        description = optional(string)

        columns = list(object({
          header = string
          rows   = list(string)
        }))
      })), [])
    })), [])

    docs_sections_post = optional(list(object({
      title       = string
      description = optional(string)

      snippets = optional(list(object({
        title   = string
        content = string
      })), [])

      tables = optional(list(object({
        title       = string
        description = optional(string)

        columns = list(object({
          header = string
          rows   = list(string)
        }))
      })), [])
    })), [])

    docs_dir    = optional(string, "docs")
    readme_name = optional(string, "terraform.md")

    gitignore_entries = optional(list(string), [])
  }))

  description = "Workspaces configuration for a Terraform pipeline"
}

variable "save_files" {
  type = bool

  default = false

  description = "Whether to save files locally"
}

variable "save_gitkeep_record" {
  type = bool

  default = false

  description = "Whether to save a gitkeep record or not"
}

variable "rel_to_root" {
  type = string

  default = ""

  description = "Relative path to the repository root"
}

variable "debug_dir" {
  type = string

  default = null

  description = "Whether to save debug information to a directory or not"
}
