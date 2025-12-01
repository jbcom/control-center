locals {
  file_format = " file_format=(type='JSON')"
  tags = {
    Name      = "${var.name}-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}

terraform {
  required_providers {
    snowflake = {
      source  = "registry.terraform.io/snowflake-labs/snowflake"
      version = "0.56.3"
    }
  }
}

# Create S3 Bucket
resource "aws_s3_bucket" "s3_bucket" {
  bucket = "fsc-${var.env}-${var.name}-analytics"
  acl    = "private"
  tags = {
    Name = "fsc-${var.env}-${var.name}"
  }
  force_destroy = true
}


# Create Kinesis Firehose Stream
resource "aws_kinesis_firehose_delivery_stream" "stream" {
  name        = "${var.env}-${var.name}"
  destination = "s3"

  s3_configuration {
    role_arn        = aws_iam_role.firehose_role.arn
    bucket_arn      = aws_s3_bucket.s3_bucket.arn
    buffer_size     = 1
    buffer_interval = 60
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/${var.env}-${var.name}"
      log_stream_name = "S3Delivery"
    }
  }
}

# Setup Snowflake
resource "snowflake_warehouse" "wh" {
  name           = "${upper(var.env)}_${upper(var.name)}_WH"
  comment        = "Warehouse for ${var.name} service in environment ${var.env}"
  warehouse_size = "XSMALL"
  auto_suspend   = 120
  auto_resume    = true
}

# resource "snowflake_database" "db" {
#   name                        = "${upper(var.env)}_${upper(var.name)}_DB"
#   comment                     = "Database for ${var.name} service in environment ${var.env}"
# }

# # creates a snowflake table. Notice the data type of column is a variant type which allows us to store json like data
# resource "snowflake_table" "events_table" {
#   database = snowflake_database.db.name
#   schema   = "PUBLIC"
#   name     = "EVENTS"
#   comment  = "Events table."
#   column {
#     name = "event"
#     type = "VARIANT"
#   }
# }

#Creates snowflake external stage from (s3) which snowpipe will read data files
#we are using aws access keys here to allow access to s3, but as mentioned earlier
#external IAM roles can be used to manage the cross account access control in a better way.
#Refer https://docs.snowflake.com/en/user-guide/data-load-snowpipe-auto-s3.html
resource "snowflake_stage" "external_stage_s3" {
  name        = "${upper(var.env)}_${upper(var.name)}_STAGE"
  url         = join("", ["s3://", aws_s3_bucket.s3_bucket.bucket, "/"])
  database    = var.database_name
  schema      = "PUBLIC"
  credentials = "AWS_KEY_ID='${aws_iam_access_key.sfuseraccesskey.id}' AWS_SECRET_KEY='${aws_iam_access_key.sfuseraccesskey.secret}'"
}

#create pipe to copy into the tweets table from the external stage
resource "snowflake_pipe" "snowpipe" {
  name     = "snowpipe"
  database = var.database_name
  schema   = "PUBLIC"
  comment  = "This is the snowpipe that will consume kinesis delivery stream channelled via the sqs."
  copy_statement = join("", [
    "copy into ",
    var.database_name, ".PUBLIC.", var.table_name,
    " from @",
    var.database_name, ".PUBLIC.", snowflake_stage.external_stage_s3.name,
    local.file_format
  ])
  auto_ingest = true
}

# Finally configure s3 bucket’s all object create events to notify snowpipe’s sqs queue
# Update your main file under our working directory to configure s3 bucket’s all object 
# create events to notify snowpipe’s sqs queue.
resource "aws_s3_bucket_notification" "bucket_notification_to_sqs" {
  bucket = aws_s3_bucket.s3_bucket.id
  queue {
    queue_arn = snowflake_pipe.snowpipe.notification_channel
    events    = ["s3:ObjectCreated:*"]
  }
}


################################################################################
# Supporting Resources
################################################################################


resource "aws_ssm_parameter" "firehose_stream_name" {
  name        = "/${var.name}/${var.env}/bi/firehose_stream_name"
  description = "Firehose Stream Name"
  type        = "SecureString"
  value       = aws_kinesis_firehose_delivery_stream.stream.name

  tags = local.tags
}

resource "aws_ssm_parameter" "firehose_stream_arn" {
  name        = "/${var.name}/${var.env}/bi/firehose_stream_arn"
  description = "Firehose Stream ARN"
  type        = "SecureString"
  value       = aws_kinesis_firehose_delivery_stream.stream.arn

  tags = local.tags
}
