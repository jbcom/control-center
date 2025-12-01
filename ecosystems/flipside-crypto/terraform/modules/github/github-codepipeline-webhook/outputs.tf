output "codepipeline_webhooks" {
  value = aws_codepipeline_webhook.github

  description = "CodePipeline webhooks"
}

output "github_webhooks" {
  value = github_repository_webhook.aws_codepipeline

  description = "GitHub webhooks"
}