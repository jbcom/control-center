module "task_label" {
  for_each = var.tasks

  source  = "cloudposse/label/null"
  version = "0.25.0"

  name = each.key

  tags = merge({
    for k, v in lookup(each.value, "tags", {}) : k => v
    }, {
    for k, v in try(each.value["tags"]["environments"][local.environment_name], {}) : k => v
    }, local.tags, {
    cluster = local.cluster_name
    service = each.key
    task    = each.key
    ECS     = "ecs"
  })

  context = var.context
}

locals {
  tasks_context = {
    for task_name, label_data in module.task_label : task_name => merge(label_data["context"], {
      for k, v in label_data : k => v if k != "context" && k != "tags"
      }, {
      tags = {
        for k, v in label_data["context"]["tags"] : title(k) => v if lower(k) != "name" && !startswith(lower(k), "aws:")
      }
    })
  }

  task_tags = {
    for task_name, context_data in local.tasks_context : task_name => context_data["tags"]
  }
}

#resource "aws_sns_topic" "task" {
#  for_each = var.tasks
#
#  name         = "${local.cluster_name}-${each.key}"
#  display_name = "${each.key} ECS task SNS topic"
#
#  tags = merge(local.task_tags[each.key], {
#    Name = "${local.cluster_name}-${each.key}"
#  })
#}

locals {
  task_environment_config = {
    for task_name, task_config in var.tasks : task_name => {
      context = local.tasks_context[task_name]

      # sns_topic_arn = aws_sns_topic.task[task_name].arn
    }
  }
}
