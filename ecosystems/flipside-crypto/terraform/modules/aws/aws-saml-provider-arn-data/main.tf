data "external" "awscli_program" {
  program = [format("%s/scripts/awsWithAssumeRole.sh", path.module)]
  query = {
    assume_role_arn    = module.assumed-role-data.assume_role_arn
    role_session_name  = "saml-provider-arn-data"
    output_file        = format("%s/temp/results.json", path.module)
    debug_log_filename = var.debug_log_filename
  }
}