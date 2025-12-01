resource "random_id" "secret_token" {
  count = var.secret_token == "" ? 1 : 0

  keepers = {
    keeper = var.name
  }

  byte_length = 40
}

locals {
  secret_token = var.secret_token == "" ? random_id.secret_token.0.dec : var.secret_token
}

resource "aws_codepipeline_webhook" "github" {
  for_each = toset(local.repositories)

  name = substr("${var.name}-${each.key}", 0, 100)

  authentication  = "GITHUB_HMAC"
  target_action   = var.target_action
  target_pipeline = var.target_pipeline

  authentication_configuration {
    secret_token = local.secret_token
  }

  filter {
    json_path    = var.filter_json_path
    match_equals = var.filter_match_equals
  }
}

resource "github_repository_webhook" "aws_codepipeline" {
  for_each = aws_codepipeline_webhook.github

  repository = each.key

  configuration {
    url          = each.value.url
    content_type = "json"
    insecure_ssl = false
    secret       = local.secret_token
  }

  events = var.events
}
