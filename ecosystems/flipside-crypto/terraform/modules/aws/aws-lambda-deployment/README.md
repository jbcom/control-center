# AWS Lambda Deployment Module

This Terraform module provides a comprehensive solution for deploying AWS Lambda functions with support for various deployment patterns and integrations.

## Features

- Lambda function deployment with support for both ZIP and container image packaging
- API Gateway integration (HTTP API)
- S3 CDN integration with CloudFront and Lambda@Edge
- ECR repository creation and Docker image building
- Lambda aliases and CodeDeploy-based deployments
- CloudWatch alarms and logging
- SSM parameter management
- Global variable overrides for consistent configuration across components

## Usage

```hcl
module "lambda_function" {
  source = "../aws/aws-lambda-deployment"

  # Context
  namespace   = "example"
  environment = "dev"
  name        = "api-function"

  # Lambda Configuration
  runtime     = "nodejs18.x"
  handler     = "index.handler"
  source_path = "./src"
  
  # API Gateway Integration
  create_api_gateway = true
  api_gateway_routes = {
    "GET /items" = {
      integration = {
        type = "AWS_PROXY"
      }
    }
  }
  
  # Global Overrides
  zone_id           = "Z1234567890ABCDEFGHIJ"
  certificate_arn   = "arn:aws:acm:us-east-1:123456789012:certificate/abcdef-1234-5678-9012-abcdefghijkl"
  global_kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/abcdef-1234-5678-9012-abcdefghijkl"
  log_retention_days = 30
}
```

## Global Variables

This module supports global variable overrides that can be used to provide consistent configuration across different components (API Gateway, S3 CDN, etc.). When a global variable is provided, it takes precedence over the component-specific variable.

### Available Global Variables

| Name | Description | Affected Components |
|------|-------------|---------------------|
| `zone_id` | ID of the Route53 hosted zone to use for DNS records | API Gateway, S3 CDN |
| `hosted_zone_name` | Name of the Route53 hosted zone to use for DNS records | API Gateway, S3 CDN |
| `private_zone` | Whether the hosted zone is private or public | API Gateway, S3 CDN |
| `evaluate_target_health` | Whether to evaluate the target health of DNS alias records | API Gateway, S3 CDN |
| `certificate_arn` | ARN of the ACM certificate to use for HTTPS | API Gateway, S3 CDN |
| `global_kms_key_arn` | ARN of the KMS key to use for encryption | Lambda, CloudWatch Logs, SSM Parameters |
| `create_kms_key` | Whether to create a KMS key for encryption | All components |
| `log_retention_days` | Number of days to retain logs in CloudWatch | Lambda, API Gateway |
| `enable_access_logging` | Whether to enable access logging for resources that support it | S3 CDN |
| `access_log_bucket_name` | Name of the S3 bucket to store access logs | S3 CDN |
| `wait_for_deployment` | Whether to wait for resource deployments to complete | S3 CDN |
| `default_ttl` | Default TTL for cached content in seconds | S3 CDN |
| `min_ttl` | Minimum TTL for cached content in seconds | S3 CDN |
| `max_ttl` | Maximum TTL for cached content in seconds | S3 CDN |

### How Global Variables Work

When you provide a global variable, the module uses it to override the corresponding component-specific variable. For example:

```hcl
module "lambda_function" {
  source = "../aws/aws-lambda-deployment"
  
  # ... other configuration ...
  
  # Component-specific variables
  api_gateway_domain_name_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/component-specific"
  s3_cdn_acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/component-specific"
  
  # Global override - this will take precedence over both component-specific variables
  certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/global-override"
}
```

In this example, both API Gateway and S3 CDN will use the certificate specified by `certificate_arn` instead of their component-specific certificate ARNs.

## KMS Key Integration

The module supports creating and using KMS keys for encrypting resources. You can either provide an existing KMS key ARN using the `global_kms_key_arn` variable, or have the module create a new KMS key by setting `create_kms_key` to `true`.

When a KMS key is created, it will be configured with appropriate policies for the resources that need to use it, such as Lambda functions, API Gateway, S3 buckets, CloudFront distributions, and CloudWatch Logs.

### KMS Key Configuration

```hcl
module "lambda_function" {
  source = "../aws/aws-lambda-deployment"
  
  # ... other configuration ...
  
  # Create a new KMS key
  create_kms_key = true
  kms_key_name = "my-lambda-key"
  kms_key_description = "KMS key for Lambda encryption"
  
  # Configure KMS key policies
  kms_key_include_lambda_policy = true
  kms_key_include_api_gateway_policy = true
  kms_key_include_s3_policy = true
  kms_key_include_cloudfront_policy = true
  kms_key_include_lambda_edge_policy = true
  kms_key_include_cloudwatch_logs_policy = true
}
```

## DNS Management

The module includes a centralized DNS management system that can create Route53 records for both API Gateway and S3 CDN resources. This system uses the global variables to determine which hosted zone to use and how to configure the DNS records.

### API Gateway DNS

When `create_api_gateway`, `api_gateway_create_domain_name`, and `api_gateway_create_domain_records` are all set to `true`, the module will create a Route53 record for the API Gateway domain name.

### S3 CDN DNS

When `create_s3_cdn` and `s3_cdn_dns_alias_enabled` are set to `true`, the module will create Route53 records for the S3 CDN aliases. If `s3_cdn_ipv6_enabled` is also set to `true`, the module will create both A and AAAA records.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `create_api_gateway` | Whether to create an API Gateway for the Lambda function | `bool` | `false` | no |
| `create_s3_cdn` | Whether to create an S3 CDN for the Lambda function | `bool` | `false` | no |
| `create_alias` | Whether to create a Lambda alias | `bool` | `true` | no |
| `create_deploy` | Whether to create a CodeDeploy deployment | `bool` | `false` | no |
| ... | ... | ... | ... | ... |

## Outputs

| Name | Description |
|------|-------------|
| `lambda_function_arn` | The ARN of the Lambda function |
| `lambda_function_name` | The name of the Lambda function |
| `lambda_function_version` | The version of the Lambda function |
| `lambda_function_url` | The URL of the Lambda function (if enabled) |
| `api_gateway_api_id` | The ID of the API Gateway API (if created) |
| `api_gateway_api_endpoint` | The endpoint URL of the API Gateway API (if created) |
| `api_gateway_domain_name` | The custom domain name of the API Gateway API (if created) |
| `s3_cdn_cloudfront_distribution_id` | The ID of the CloudFront distribution (if created) |
| `s3_cdn_cloudfront_distribution_domain_name` | The domain name of the CloudFront distribution (if created) |
| `s3_cdn_bucket_name` | The name of the S3 bucket (if created) |
| ... | ... |
