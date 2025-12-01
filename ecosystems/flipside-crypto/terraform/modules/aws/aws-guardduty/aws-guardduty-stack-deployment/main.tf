locals {
  guardduty_config = var.context["guardduty"]["configuration"]
}

resource "aws_cloudformation_stack" "defaults" {
  name = var.stack_name

  capabilities = var.stack_capabilities

  template_body = templatefile("${path.module}/cfn-templates/${var.template_name}.cfntemplate", local.guardduty_config)

  tags = var.context["tags"]
}

locals {
  records_config = aws_cloudformation_stack.defaults.outputs
}

module "permanent_record" {
  source = "../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
