resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  bucket_name = replace("fsc-cdn-${var.name}-${random_id.bucket_suffix.hex}", ".", "-")

  tags = merge(var.context["tags"], {
    Name = local.bucket_name
  })
}

resource "random_id" "refer-secret" {
  prefix = var.name

  byte_length = 32
}

resource "aws_s3_bucket" "default" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = local.tags
}

locals {
  bucket_id  = aws_s3_bucket.default.id
  bucket_arn = aws_s3_bucket.default.arn
}

resource "aws_s3_bucket_website_configuration" "default" {
  bucket = local.bucket_id

  redirect_all_requests_to {
    host_name = replace(var.redirect_target, "/^https?:///", "")
    protocol  = "https"
  }
}

data "aws_iam_policy_document" "default" {
  statement {
    sid = "AllowCFOriginAccess"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${local.bucket_arn}/*",
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:UserAgent"

      values = [
        local.refer_secret,
      ]
    }

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "default" {
  bucket = local.bucket_id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "default" {
  bucket = local.bucket_id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "default" {
  bucket = local.bucket_id
  policy = data.aws_iam_policy_document.default.json

  depends_on = [
    aws_s3_bucket_ownership_controls.default,
    aws_s3_bucket_public_access_block.default,
  ]
}

locals {
  refer_secret = base64sha512(random_id.refer-secret.hex)
}

resource "aws_cloudfront_distribution" "main" {
  provider     = aws.cloudfront
  http_version = "http2and3"

  origin {
    origin_id   = "origin-${var.name}"
    domain_name = aws_s3_bucket_website_configuration.default.website_endpoint

    # https://docs.aws.amazon.com/AmazonCloudFront/latest/
    # DeveloperGuide/distribution-web-values-specify.html
    custom_origin_config {
      # "HTTP Only: CloudFront uses only HTTP to access the origin."
      # "Important: If your origin is an Amazon S3 bucket configured
      # as a website endpoint, you must choose this option. Amazon S3
      # doesn't support HTTPS connections for website endpoints."
      origin_protocol_policy = "http-only"

      http_port  = "80"
      https_port = "443"

      # TODO: given the origin_protocol_policy set to `http-only`,
      # "If the origin is an Amazon S3 bucket, CloudFront always uses TLSv1.2."
      origin_ssl_protocols = ["TLSv1.2"]
    }

    # s3_origin_config is not compatible with S3 website hosting, if this
    # is used, /news/index.html will not resolve as /news/.
    # https://www.reddit.com/r/aws/comments/6o8f89/can_you_force_cloudfront_only_access_while_using/
    # s3_origin_config {
    #   origin_access_identity = "${aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path}"
    # }
    # Instead, we use a secret to authenticate CF requests to S3 policy.
    # Not the best, but...
    custom_header {
      name  = "User-Agent"
      value = local.refer_secret
    }
  }

  enabled = true

  aliases = [var.name]

  price_class = "PriceClass_100"

  default_cache_behavior {
    target_origin_id = "origin-${var.name}"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true

    forwarded_values {
      query_string = true

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 300
    max_ttl                = 1200
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  web_acl_id = var.web_acl_id

  tags = merge(var.context["tags"], {
    Name = var.name
  })
}
