data "aws_iam_policy_document" "opensearch-public-allow-http" {
  for_each = module.opensearch-public

  statement {
    principals {
      identifiers = ["*"]
      type        = "AWS"
    }

    actions = [
      "es:ESHttp*",
    ]

    resources = [
      format("%s/*", each.value["domain_arn"]),
    ]
  }
}

resource "aws_elasticsearch_domain_policy" "opensearch-public-allow-http" {
  for_each = module.opensearch-public

  domain_name = each.value["domain_name"]

  access_policies = data.aws_iam_policy_document.opensearch-public-allow-http[each.key].json
}