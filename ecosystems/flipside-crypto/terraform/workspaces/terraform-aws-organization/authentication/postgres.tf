locals {
  postgres_credentials = local.credentials_data["postgres"]

  product_eng_velocity_mark_2_cluster_credentials_data = local.postgres_credentials["product-eng-velocity-mark-2"]
}

provider "postgresql" {
  alias = "product-eng-velocity-mark-2-cluster"

  scheme   = "awspostgres"
  host     = local.product_eng_velocity_mark_2_cluster_credentials_data["host"]
  username = local.product_eng_velocity_mark_2_cluster_credentials_data["username"]
  port     = 5432
  password = local.product_eng_velocity_mark_2_cluster_credentials_data["password"]
  database = local.product_eng_velocity_mark_2_cluster_credentials_data["database"]

  superuser = false
}

# Create a read-only user for Hevo data pipeline operations using the module
module "hevo_readonly_user" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//postgres/postgres-hevo-ro-user"

  providers = {
    postgresql.postgres = postgresql.product-eng-velocity-mark-2-cluster
  }

  cluster_name    = "product-eng-velocity-mark-2"
  database_name   = local.product_eng_velocity_mark_2_cluster_credentials_data["database"]
  schema_name     = "public"
  username_prefix = "prod_platform_api_db_"
  table_owner     = local.product_eng_velocity_mark_2_cluster_credentials_data["username"]
  roles           = ["rds_replication"]

  tags = {
    Environment = "production"
    Purpose     = "Hevo Data Pipeline"
  }
}
