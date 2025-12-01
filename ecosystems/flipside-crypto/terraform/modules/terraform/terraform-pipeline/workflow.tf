locals {
  workflow_template_dir = "${path.module}/templates/workflow"

  call_workflows = var.workflow.call

  call_workflow_jobs_yaml = merge({
    for workflow_path in local.call_workflows["before"] :
    format("%s-before", replace(trimsuffix(basename(workflow_path), ".yml"), "_", "-")) => {
      uses    = "./${workflow_path}"
      secrets = "inherit"
    }
    }, {
    for workflow_path in local.call_workflows["after"] :
    format("%s-after", replace(trimsuffix(basename(workflow_path), ".yml"), "_", "-")) => {
      uses    = "./${workflow_path}"
      secrets = "inherit"
      needs = [
        for _, workspace_config in local.workspaces_template_variables_config : workspace_config["job_name"]
      ]
    }
  })

  non_pull_request_base_dependencies = [
    for job_name, _ in local.call_workflow_jobs_yaml : job_name if endswith(job_name, "-before")
  ]

  workspaces_depending_on_conditional_workspaces = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => anytrue([
      for dependant_workspace_name in workspace_config["dependencies"] :
      (try(local.workspaces_template_variables_config[dependant_workspace_name]["conditions"], {}) != {})
    ])
  }

  jobs = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_config["job_name"] =>
    merge(workspace_config, {
      workspace_dir                               = local.workspaces_workspace_dir[workspace_name]
      job_conditional_key                         = try(coalesce(workspace_config["conditions"]["key"]), "apply-${workspace_name}")
      workspace_depends_on_conditional_workspaces = local.workspaces_depending_on_conditional_workspaces[workspace_name]
    })
  }
}

module "latest_terragrunt_version" {
  source = "../../terragrunt/terragrunt-get-latest-terragrunt-version"
}

locals {
  job_inputs = [
    for job_name, job_config in local.jobs : merge({
      required    = false
      default     = true
      description = "Whether to apply the ${job_name} Terraform workspace"
      }, job_config["conditions"], {
      type = "boolean"
      key  = job_config["job_conditional_key"]
    }) if job_config["conditions"] != {}
  ]

  raw_inputs = concat([
    for input_name, input_config in var.workflow.inputs : merge(input_config, {
      key = try(coalesce(input_config["key"]), input_name)
    })
    ], local.job_inputs, var.workflow.allow_build_and_push_only ? [{
      required    = false
      default     = false
      description = "Whether to only build and push any Docker image(s) for this pipeline without applying any Terraform"
      type        = "boolean"
      key         = "build-and-push-only"
  }] : [])

  inputs = {
    for input_config in local.raw_inputs : input_config["key"] => input_config
  }

  tfvar_inputs = {
    for input_key in keys(local.inputs) : input_key => replace(input_key, "-", "_")
  }

  base_steps_yaml = {
    for job_name, workspace_config in local.jobs : job_name =>
    yamldecode(templatefile("${local.workflow_template_dir}/steps.yaml.tpl", merge(var.workflow, workspace_config, {
      use_oidc_auth             = var.workflow.use_oidc_auth
      use_https_git_auth        = var.workflow.use_https_git_auth
      enable_docker_images      = length(keys(workspace_config["docker_images"])) > 0
      allow_build_and_push_only = var.workflow.allow_build_and_push_only
      terragrunt_version        = module.latest_terragrunt_version.version
      tfvar_inputs              = local.tfvar_inputs
      registry_accounts = distinct([
        for _, repository_config in workspace_config["docker_images"] : repository_config["account_id"]
      ])
    })))
  }

  steps_yaml = {
    for job_name, steps_yaml in local.base_steps_yaml : job_name => {
      pull_request     = concat(steps_yaml["setup"], steps_yaml["pull_request"])
      not_pull_request = concat(steps_yaml["setup"], steps_yaml["push"], steps_yaml["save"])
    }
  }

  base_jobs_yaml = {
    for job_name, workspace_config in local.jobs : job_name => {
      pull_request = merge(yamldecode(templatefile("${local.workflow_template_dir}/job.yaml.tpl", workspace_config)), {
        steps = local.steps_yaml[job_name]["pull_request"]
      })

      not_pull_request = merge(yamldecode(templatefile("${local.workflow_template_dir}/job.yaml.tpl", merge(workspace_config, {
        dependencies = distinct(concat(local.non_pull_request_base_dependencies, workspace_config["dependencies"]))
        }))), {
        steps = local.steps_yaml[job_name]["not_pull_request"]
      })
    }
  }

  release = var.workflow["release"]

  post_job_dependencies = distinct(concat(keys(local.call_workflow_jobs_yaml), keys(local.base_jobs_yaml)))

  raw_publish_job_yaml = yamldecode(templatefile("${local.workflow_template_dir}/publish.yaml.tpl", merge(local.release, {
    dependencies = local.post_job_dependencies
  })))

  base_publish_job_yaml = {
    publish    = local.raw_publish_job_yaml
    no_publish = {}
  }

  publish_job_yaml_key = local.release["publish"] ? "publish" : "no_publish"

  publish_job_yaml = local.base_publish_job_yaml[local.publish_job_yaml_key]

  raw_dispatch_job_data = {
    for dispatch_job in var.workflow.dispatch : replace(coalesce(dispatch_job["job_name"], join("-", [
      "dispatch",
      dispatch_job["organization"],
      dispatch_job["repository"],
      dispatch_job["branch"],
      trimsuffix(dispatch_job["workflow"], ".yml"),
    ])), "_", "-") => dispatch_job
  }

  dispatch_job_yaml = [
    for job_name, job_data in local.raw_dispatch_job_data :
    yamldecode(templatefile("${local.workflow_template_dir}/dispatch.yaml.tpl", merge(job_data, {
      job_name     = job_name
      dependencies = local.post_job_dependencies
    })))
  ]

  jobs_yaml = {
    pull_request = {
      for job_name, job_yaml in local.base_jobs_yaml : job_name => job_yaml["pull_request"]
    }

    not_pull_request = merge(local.call_workflow_jobs_yaml, {
      for job_name, job_yaml in local.base_jobs_yaml : job_name => job_yaml["not_pull_request"]
    }, local.publish_job_yaml, local.dispatch_job_yaml...)
  }

  triggers_autopopulate = var.workflow.autopopulate
  triggers_config       = var.workflow.triggers

  trigger_dirs = formatlist("%s/**", distinct(concat(local.triggers_config["directories"], local.triggers_autopopulate["paths"] ? [
    for _, workspace_data in local.jobs : workspace_data["workspace_dir"]
  ] : [])))

  trigger_files = distinct(compact(flatten(concat(local.triggers_config["files"], local.triggers_autopopulate["paths"] ? [
    for _, workspace_data in local.jobs : concat([
      try(workspace_data["bind_to_context"]["merge_record"], ""),
    ], try(workspace_data["bind_to_context"]["merge_records"], []))
  ] : []))))

  triggers_data = merge(local.triggers_config, {
    directories = local.trigger_dirs
    files       = local.trigger_files
    paths = distinct(concat(local.triggers_config["paths"], [
      for path in distinct(concat(local.trigger_dirs, local.trigger_files)) : join("/", [
        for chunk in split("/", path) : chunk if chunk != "."
      ]) if try(coalesce(path), null) != null
    ]))

    branches = local.triggers_autopopulate["branches"] ? distinct(concat(local.triggers_config["branches"], [
      for _, workspace_data in local.jobs : workspace_data["workspace_branch"]
    ])) : local.triggers_config["branches"]
  })

  pull_requests_config = var.workflow.pull_requests

  workflow_name     = replace(var.workflow.workflow_name, "_", "-")
  concurrency_group = coalesce(var.workflow.concurrency_group, local.workflow_name)

  # Build secrets from both doppler and vault required environment variables
  required_secrets = {
    for var_name in concat(
      local.doppler_config.required_environment_variables,
      local.vault_config.required_environment_variables
    ) :
    upper(var_name) => upper(var_name)
  }

  workflow_secrets = merge(
    local.required_secrets,
    var.workflow.secrets,
    {
      for key in var.workflow.secret_keys : key => key
    }
  )

  workflow_env_vars = merge({
    TF_PLUGIN_CACHE_DIR : "/tmp/.terraform.d/plugin-cache"
    TERRAGRUNT_DOWNLOAD : "/tmp/.terragrunt.d"
    TF_IN_AUTOMATION : true
  }, var.workflow.environment_variables)
}

module "push_workflow" {
  source = "../../github/github-build-github-actions-workflow"

  workflow_name     = local.workflow_name
  concurrency_group = local.concurrency_group

  environment_variables = local.workflow_env_vars

  secrets = local.workflow_secrets

  events = merge(var.workflow.events, {
    pull_request = false
  })

  triggers = local.triggers_data

  inputs = local.inputs

  jobs = local.jobs_yaml["not_pull_request"]

  use_oidc_auth = var.workflow.use_oidc_auth

  log_file_name = "${local.workflow_name}-push-workflow.log"
}

module "pull_request_workflow" {
  count = var.workflow.events.pull_request ? 1 : 0

  source = "../../github/github-build-github-actions-workflow"

  workflow_name     = "${local.workflow_name}-pull-request"
  concurrency_group = local.concurrency_group

  environment_variables = local.workflow_env_vars

  secrets = local.workflow_secrets

  events = {
    push         = false
    pull_request = true
    release      = false
    schedule     = []
    call         = false
    dispatch     = false
  }

  triggers = local.triggers_data

  jobs = local.jobs_yaml["pull_request"]

  use_oidc_auth = var.workflow.use_oidc_auth



  log_file_name = "${local.workflow_name}-push-workflow.log"
}

locals {
  base_workflow_yaml = {
    "${local.workflow_name}.yml"              = module.push_workflow.workflow
    "${local.workflow_name}-pull-request.yml" = try(module.pull_request_workflow[0].workflow, "")
  }

  workflow_yaml = {
    for file_name, workflow_data in local.base_workflow_yaml : file_name => workflow_data if try(coalesce(workflow_data), null) != null
  }

  workflow_files_data = [
    {
      ".github/workflows" = local.workflow_yaml
    }
  ]
}
