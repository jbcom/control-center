locals {
  # just to make the conditional more readable below
  current_provider_role_is_assumed                        = data.aws_iam_session_context.current.issuer_name != null
  current_provider_role_arn                               = data.aws_iam_session_context.current.issuer_arn
  underlying_role_arn                                     = data.external.aws_iam_session_context.result.issuer_arn
  underlying_role_is_different_from_assumed_provider_role = local.current_provider_role_arn != local.underlying_role_arn
  should_use_assume_role                                  = local.current_provider_role_is_assumed && local.underlying_role_is_different_from_assumed_provider_role
}