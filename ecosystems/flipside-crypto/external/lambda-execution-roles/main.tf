data "external" "query" {
  program = ["python", "${path.module}/bin/lambda_function_role_arns.py"]

  query = {
    execution_role_arn = var.execution_role_arn
  }
}

locals {
  roles_data = {
    for function_name, role_arns in jsondecode(base64decode(data.external.query.result["roles"])) : function_name => role_arns if !startswith(function_name, "aws-controltower")
  }
}