#!/bin/bash

# Define the moves in a list
moves=(
  "module.base.module.s3_buckets-private[\"fsc-compass-dev\"] module.base.module.fsc_compass_dev_s3_bucket"
  "module.base.module.efs_filesystems-private[\"compass-prod\"] module.base.module.compass_prod_efs_filesystem"
  "module.base.module.databases-public[\"compass-prod\"] module.base.module.compass_prod_rds_database"
  "module.base.module.s3_buckets-private[\"fsc-compass-prod\"] module.base.module.fsc_compass_prod_s3_bucket"
  "module.base.module.s3_buckets-private[\"fsc-compass-stg\"] module.base.module.fsc_compass_stg_s3_bucket"
  "module.base.module.efs_filesystems-private[\"compass-stg\"] module.base.module.compass_stg_efs_filesystem"
  "module.base.module.databases-public[\"compass-stg\"] module.base.module.compass_stg_rds_database"
  "module.base.module.s3_buckets-private[\"fsc-analytics\"] module.base.module.fsc_analytics_s3_bucket"
  "module.base.module.s3_buckets-private[\"fsc-compass-lambda-artifacts\"] module.base.module.fsc_compass_lambda_artifacts_s3_bucket"
)

# Then, move the old module states to the new ones
for move in "${moves[@]}"; do
  from=$(echo $move | awk '{print $1}')
  to=$(echo $move | awk '{print $2}')
  echo "Moving state from '$from' to '$to'"
  terraform state mv "$from" "$to"
done

echo "State moves completed."
