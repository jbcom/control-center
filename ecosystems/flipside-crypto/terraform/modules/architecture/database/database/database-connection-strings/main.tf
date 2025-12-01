module "dsn" {
  source = "../../secret"

  name = "/connection-strings/databases/${var.secret_suffix}/dsn"

  secret = format(
    "user=%s password=%s host=%s port=%s database=%s schema=%s",
    var.config["master_username"],
    var.config["password"],
    var.config["endpoint"],
    var.config["db_port"],
    var.config["database_name"],
    var.config["schema"]
  )

  policy = var.secret_policy

  kms_key_arn = var.kms_key_arn

  tags = var.tags
}

module "url" {
  source = "../../secret"

  name = "/connection-strings/databases/${var.secret_suffix}/url"

  secret = format(
    "postgres://%s:%s@%s:%s/%s?schema=%s",
    var.config["master_username"],
    var.config["password"],
    var.config["endpoint"],
    var.config["db_port"],
    var.config["database_name"],
    var.config["schema"]
  )

  policy = var.secret_policy

  kms_key_arn = var.kms_key_arn

  tags = var.tags
}