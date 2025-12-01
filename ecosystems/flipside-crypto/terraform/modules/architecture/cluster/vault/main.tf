locals {
  shared_san = "fsc-vault.systems"

  resource_id = var.context["id"]

  tags = merge(var.context["tags"], {
    Name = local.resource_id
  })

  kms_key_arn = var.context["cluster_secrets"]["kms_key_arn"]
}

resource "kubernetes_namespace_v1" "default" {
  metadata {
    annotations = {
      name = "vault"
    }

    name = "vault"
  }
}

locals {
  namespace = kubernetes_namespace_v1.default.metadata[0].name
}

resource "helm_release" "vault_server" {
  name             = "server"
  repository       = "https://helm.releases.hashicorp.com"
  chart            = "vault"
  version          = "0.31.0"
  namespace        = local.namespace
  create_namespace = false

  recreate_pods   = true
  cleanup_on_fail = true

  wait          = true
  wait_for_jobs = true

  values = [
    templatefile("${path.module}/templates/values.yaml", {
      shared_san           = local.shared_san
      region               = local.region
      kms_key_arn          = local.kms_key_arn
      s3_bucket_id         = local.s3_bucket_id
      dynamodb_table_name  = local.dynamodb_table_name
      certificate_arn      = local.certificate_arn
      service_account_name = local.service_account_name
      secret_name          = local.tls_secret
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.default,
    aws_s3_bucket_replication_configuration.vault_data,
    aws_acm_certificate.vault,
    kubernetes_service_account_v1.vault_server,
  ]
}