# Guards workspace - Lambda functions for AWS Organization governance
# This workspace manages guard lambdas that extend beyond what SCPs can do

# Deploy all guards defined in config/guards/
module "guards" {
  for_each = local.context.guards

  source = "../../modules/aws-guard-lambda-deployment"

  # Our blackbox context and guard name
  context = local.context
  name    = each.key

  # Path variables with defaults
  rel_to_root  = "../.."
  base_src_dir = "src/guards"
}
