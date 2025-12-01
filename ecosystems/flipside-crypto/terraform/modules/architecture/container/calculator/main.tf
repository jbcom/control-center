locals {
  cluster_accounts_by_environment_data = var.context["cluster_accounts_by_environment"]

  reusable_workflow_template = "FlipsideCrypto/gitops/.github/workflows/%s.yml@main"

  live_environments = var.context["live_environments"]

  task_base_defaults = {
    environments = local.live_environments

    deployment = {}

    autoscaling = {}

    alarms = {}

    spot = {
      enabled = false
      weight  = 0
    }

    circuit_breaker = {}

    wait_for_steady_state = false

    cpu            = 256
    cpu_cushion    = 256
    memory         = 512
    memory_cushion = 512
    scale          = 1

    ephemeral_storage_size = 0

    enabled  = true
    exposed  = false
    launched = false

    tags = {}

    volumes = {}

    secrets = {}

    environment_variables = {}

    permissions = {}

    pipeline = {}

    approle = {}
  }

  task_deployment_defaults = {
    desired_count           = 1
    maximum_percent         = 100
    minimum_healthy_percent = 0
  }

  task_autoscaling_defaults = {
    enabled = false

    dimension = "memory"

    min_capacity = 1
    max_capacity = 1

    scale_up_adjustment = 1
    scale_up_cooldown   = 60

    scale_down_adjustment = -1
    scale_down_cooldown   = 300
  }

  task_alarm_defaults = {
    enabled = true

    alb_target_group_3xx_threshold           = 25
    alb_target_group_4xx_threshold           = 25
    alb_target_group_5xx_threshold           = 25
    alb_target_group_response_time_threshold = 0.5
    alb_target_group_period                  = 300
    alb_target_group_evaluation_periods      = 1

    ecs_cpu_utilization_high_alarm_actions      = []
    ecs_cpu_utilization_high_ok_actions         = []
    ecs_cpu_utilization_high_threshold          = 80
    ecs_cpu_utilization_high_evaluation_periods = 1
    ecs_cpu_utilization_high_period             = 300

    ecs_cpu_utilization_low_alarm_actions      = []
    ecs_cpu_utilization_low_ok_actions         = []
    ecs_cpu_utilization_low_threshold          = 20
    ecs_cpu_utilization_low_evaluation_periods = 1
    ecs_cpu_utilization_low_period             = 300

    ecs_memory_utilization_high_alarm_actions      = []
    ecs_memory_utilization_high_ok_actions         = []
    ecs_memory_utilization_high_threshold          = 80
    ecs_memory_utilization_high_evaluation_periods = 1
    ecs_memory_utilization_high_period             = 300

    ecs_memory_utilization_low_alarm_actions      = []
    ecs_memory_utilization_low_ok_actions         = []
    ecs_memory_utilization_low_threshold          = 20
    ecs_memory_utilization_low_evaluation_periods = 1
    ecs_memory_utilization_low_period             = 300
  }

  task_circuit_breaker_defaults = {
    enabled  = false
    rollback = false
  }

  task_approle_defaults = {
    enabled       = false
    role_id_key   = "VAULT_ROLE_ID"
    secret_id_key = "VAULT_SECRET_ID"
  }

  task_layers_config = try(coalesce(var.layers, var.context["layers"]), {})
}

module "raw_task_config" {
  for_each = var.context.tasks

  source = "../../../utils/deepmerge"

  source_maps = concat([
    for layer in distinct(compact(flatten(try(concat(each.value["layers"], []), [each.value["layers"]], [])))) :
    local.task_layers_config[layer] if contains(keys(local.task_layers_config), layer)
    ], [
    each.value,
    {
      name = replace(lookup(each.value, "name", each.key), "/\\W|_|\\s/", "-")

      containers = {
        for container_name, container_definition in lookup(each.value, "containers", {}) : container_name => merge(container_definition, {
          name = replace(lookup(container_definition, "name", container_name), "/\\W|_|\\s/", "-")
        })
      }
    }
  ])

  log_file_name = "${each.key}-raw-task-config.log"
}

locals {
  raw_task_config = {
    for task_name, task_config in module.raw_task_config : lookup(task_config.merged_maps, "name", task_name) => merge(local.task_base_defaults, task_config.merged_maps)
  }

  base_task_config = {
    for task_name, task_config in local.raw_task_config : task_name => merge(task_config, {
      containers = {
        for container_name, container_definition in task_config["containers"] : container_name => merge(container_definition, {
          network_name = lookup(container_definition, "network_name", (task_name == container_name ? task_name : "${task_name}-${container_name}"))
        })
      }
    })
  }

  container_defaults = {
    command    = null
    entrypoint = null

    container_depends_on = null

    disable_networking = null

    dns_search_domains = null
    dns_servers        = null

    essential = true

    extra_hosts = null

    links = null

    linux_parameters = null

    readonly_root_filesystem = false

    start_timeout = null
    stop_timeout  = null

    system_controls = null

    ulimits = null

    user = null

    volumes_from = null

    working_directory = null

    port_mappings = []
  }

  container_health_check_defaults = {
    path                = "/"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    matcher             = "200-399"
    timeout             = 10
  }

  container_ingress_defaults = {
    protocol         = "HTTP"
    protocol_version = "HTTP1"
  }

  task_config = {
    for task_name, task_config in local.base_task_config : task_name => merge(task_config, {
      exposed  = task_config["enabled"] ? task_config["exposed"] : false
      launched = task_config["enabled"] ? task_config["launched"] : false

      autoscaling = merge(local.task_autoscaling_defaults, task_config["autoscaling"])

      alarms = merge(local.task_alarm_defaults, task_config["alarms"])

      circuit_breaker = merge(local.task_circuit_breaker_defaults, task_config["circuit_breaker"])

      approle = merge(local.task_approle_defaults, task_config["approle"])

      deployment = merge(local.task_deployment_defaults, task_config["deployment"])

      containers = {
        for _, container_definition in task_config["containers"] : container_definition["name"] => merge(local.container_defaults, container_definition, {
          enabled         = lookup(container_definition, "enabled", task_config["enabled"])
          repository_name = lookup(container_definition, "repository_name", container_definition["name"])

          health_check = merge(local.container_health_check_defaults, lookup(container_definition, "health_check", {}))
          ingress      = merge(local.container_ingress_defaults, lookup(container_definition, "ingress", {}))
        })
      }
    })
  }
}

module "pipeline_tasks" {
  source = "../../../utils/deepmerge"

  source_maps = flatten([
    for task_name, task_config in local.task_config : {
      (task_config["pipeline"]) = [task_name]
    } if try(coalesce(task_config["pipeline"]), null) != null
  ])

  log_file_name = "pipeline-tasks.log"
}

module "task_cpu_and_memory" {
  for_each = local.task_config

  source = "./calculator-resources"

  identifier = each.key

  total_cpu   = each.value["cpu"]
  unit_cpu    = lookup(each.value, "unit_cpu", null)
  cpu_cushion = each.value["cpu_cushion"]

  total_memory   = each.value["memory"]
  unit_memory    = lookup(each.value, "unit_memory", null)
  memory_cushion = each.value["memory_cushion"]

  scale = each.value["scale"]
}

locals {
  merged_tasks_config = {
    for task_name, task_config in local.task_config : task_name => merge(task_config, {
      cpu    = module.task_cpu_and_memory[task_name].total_cpu
      memory = module.task_cpu_and_memory[task_name].total_memory

      containers = {
        for container_name, container_definition in task_config["containers"] : container_definition["name"] => merge(container_definition, {
          exposed  = container_definition["enabled"] ? lookup(container_definition, "exposed", task_config["exposed"]) : false
          launched = container_definition["enabled"] ? lookup(container_definition, "launched", task_config["launched"]) : false

          cpu    = tonumber(lookup(container_definition, "cpu", 0)) > module.task_cpu_and_memory[task_name].unit_cpu ? module.task_cpu_and_memory[task_name].unit_cpu : lookup(container_definition, "cpu", null)
          memory = tonumber(lookup(container_definition, "memory", 0)) > module.task_cpu_and_memory[task_name].unit_memory ? module.task_cpu_and_memory[task_name].unit_memory : lookup(container_definition, "memory", null)
        })
      }
    })
  }
}

module "task_networking" {
  for_each = local.merged_tasks_config

  source = "./calculator-networking"

  identifier = each.key
  config     = each.value["containers"]
}

locals {
  pipeline_tasks = module.pipeline_tasks.merged_maps

  task_environments = distinct(flatten([
    for _, task_config in local.merged_tasks_config : task_config["environments"]
  ]))

  tasks_environment_raw_config = {
    for environment in local.task_environments : environment => {
      for task_name, task_config in local.merged_tasks_config : task_name => merge(task_config, {
        containers = {
          for container_name, container_definition in task_config["containers"] : container_definition["name"] => merge(container_definition, {
            hostname = format("%s.%s", replace(lookup(container_definition, "hostname", container_definition["network_name"]), "_", "-"), local.cluster_accounts_by_environment_data[environment]["subdomain"])

            ingress = module.task_networking[task_name].networking[container_name]["ingress"]

            port_mappings = module.task_networking[task_name].networking[container_name]["port_mappings"]
          })
        }
      }) if contains(task_config["environments"], environment)
    }
  }
}

module "task_secrets" {
  for_each = local.tasks_environment_raw_config

  source = "./calculator-environment"

  environment_name = each.key

  config = each.value

  data_key = "secrets"
}

module "task_environment_variables" {
  for_each = local.tasks_environment_raw_config

  source = "./calculator-environment"

  environment_name = each.key

  config = each.value

  data_key = "environment_variables"
}

locals {
  tasks_environment_base_config = {
    for environment, tasks_config in local.tasks_environment_raw_config : environment => {
      for task_name, task_config in tasks_config : task_name => merge(task_config, {
        secrets = module.task_secrets[environment].data[task_name]

        environment_variables = module.task_environment_variables[environment].data[task_name]
      })
    }
  }
}

module "task_merges" {
  for_each = local.tasks_environment_base_config

  source = "./calculator-merges"

  config = each.value

  rel_to_root = var.rel_to_root
}

module "permissions_config" {
  for_each = module.task_merges

  source = "./calculator-permissions"

  environment_name = each.key

  config = each.value.config

  account_data = local.cluster_accounts_by_environment_data[each.key]

  context = var.context

  rel_to_root = var.rel_to_root
}

locals {
  tasks_environment_config = {
    for environment, tasks_config in module.task_merges : environment => {
      for task_name, task_config in tasks_config["config"] : replace(task_name, "/\\W|_|\\s/", "-") =>
      merge(task_config, {
        name        = replace(task_name, "/\\W|_|\\s/", "-")
        permissions = module.permissions_config[environment].config[task_name]

        containers = {
          for container_name, container_definition in task_config["containers"] :
          replace(container_name, "/\\W|_|\\s/", "-") => merge(container_definition, {
            name = replace(container_name, "/\\W|_|\\s/", "-")
          })
        }
      })
    }
  }

  tasks_environment_pipeline_raw_config = {
    for environment, tasks_config in local.tasks_environment_config : environment => {
      for pipeline_name, pipeline_tasks in local.pipeline_tasks : pipeline_name =>
      merge(var.context["pipelines"][pipeline_name], {
        shared_pipeline_name = pipeline_name

        tasks = {
          for task_name in distinct(pipeline_tasks) : task_name => tasks_config[task_name]
          if contains(keys(tasks_config), task_name) && contains(keys(var.context["pipelines"]), pipeline_name)
        }
      })
    }
  }

  tasks_environment_pipeline_base_config = merge(flatten([
    for environment, pipelines_config in local.tasks_environment_pipeline_raw_config : [
      for pipeline, pipeline_config in pipelines_config : {
        "${environment}-${pipeline}" = merge(pipeline_config, {
          environment = environment
          repository_names = distinct(compact(flatten([
            for _, task_config in pipeline_config["tasks"] : [
              for _, container_config in task_config["containers"] : container_config["repository_name"]
              if lookup(container_config, "image", "") == ""
            ]
          ])))
        })
      }
    ]
  ])...)

  tasks_environment_pipeline_config = {
    for pipeline_name, pipeline_config in local.tasks_environment_pipeline_base_config : pipeline_name => merge(pipeline_config, {
      repositories = {
        for repository_name in pipeline_config["repository_names"] : repository_name =>
        merge(local.cluster_accounts_by_environment_data[pipeline_config["environment"]], try(coalesce(pipeline_config["build"]), {}))
      }
    })
  }
}

module "task_environment_pipelines" {
  for_each = local.tasks_environment_pipeline_config

  source = "./calculator-terraform-pipeline"

  pipeline_name   = each.key
  pipeline_config = each.value

  base_terraform_workspace_config          = var.base_terraform_workspace_config
  base_terraform_workflow_config           = var.base_terraform_workflow_config
  base_nested_root_dir_template            = var.base_nested_root_dir_template
  base_nested_backend_path_prefix_template = var.base_nested_backend_path_prefix_template
  base_default_context_binding             = var.base_default_context_binding

  context = var.context

  rel_to_root = var.rel_to_root
}
