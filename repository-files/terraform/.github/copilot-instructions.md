# Terraform Copilot Instructions

## Environment Setup

### Required Tools
```bash
# Terraform
terraform version  # Check version matches constraints

# TFLint (linting)
tflint --version

# terraform-docs (documentation)
terraform-docs --version
```

## Development Commands

### Initialization
```bash
# Initialize working directory
terraform init

# Upgrade providers
terraform init -upgrade

# Reconfigure backend
terraform init -reconfigure
```

### Validation & Planning
```bash
# Validate configuration
terraform validate

# Format check
terraform fmt -check -recursive

# Format fix
terraform fmt -recursive

# Plan changes
terraform plan

# Plan with output file
terraform plan -out=tfplan

# Plan for specific target
terraform plan -target=module.specific
```

### Applying
```bash
# Apply changes (interactive)
terraform apply

# Apply saved plan
terraform apply tfplan

# Apply without confirmation (CI/CD only)
terraform apply -auto-approve
```

### Linting
```bash
# Run TFLint
tflint --recursive

# With specific ruleset
tflint --config=.tflint.hcl
```

### Documentation
```bash
# Generate docs
terraform-docs markdown . > README.md

# Generate for module
terraform-docs markdown table --output-file README.md --output-mode inject .
```

## Code Patterns

### File Structure
```
.
├── main.tf           # Primary resources
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider/Terraform versions
├── locals.tf         # Local values
├── data.tf           # Data sources
└── modules/
    └── submodule/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Variable Definitions
```hcl
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "config" {
  description = "Complex configuration object"
  type = object({
    enabled = bool
    count   = number
    names   = list(string)
  })
}
```

### Resource Naming
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}

resource "aws_s3_bucket" "main" {
  bucket = "${local.name_prefix}-data"
  tags   = local.common_tags
}
```

### Module Usage
```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${local.name_prefix}-vpc"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  tags = local.common_tags
}
```

### Conditionals
```hcl
# Conditional resource creation
resource "aws_cloudwatch_log_group" "main" {
  count = var.enable_logging ? 1 : 0
  
  name              = "/aws/${local.name_prefix}"
  retention_in_days = var.log_retention_days
}

# Conditional in expressions
locals {
  log_group_arn = var.enable_logging ? aws_cloudwatch_log_group.main[0].arn : null
}
```

### For Each
```hcl
resource "aws_iam_user" "users" {
  for_each = toset(var.user_names)
  
  name = each.value
  tags = local.common_tags
}

# With maps
resource "aws_ssm_parameter" "params" {
  for_each = var.parameters
  
  name  = "/${var.project}/${each.key}"
  type  = each.value.type
  value = each.value.value
}
```

### Outputs
```hcl
output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_id" {
  description = "ID of the S3 bucket"
  value       = aws_s3_bucket.main.id
  sensitive   = false
}
```

## Common Issues

### State Locking
```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

### Provider Version Conflicts
```hcl
# Pin provider versions in versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Importing Existing Resources
```bash
# Import resource into state
terraform import aws_s3_bucket.main bucket-name

# Generate configuration from import
terraform plan -generate-config-out=generated.tf
```

### Refresh State
```bash
# Refresh state from actual infrastructure
terraform refresh

# Plan with refresh disabled
terraform plan -refresh=false
```

## Best Practices

1. **Always run `terraform plan` before `apply`**
2. **Use workspaces or separate state files per environment**
3. **Store state remotely (S3, GCS, Terraform Cloud)**
4. **Lock provider versions**
5. **Use modules for reusable components**
6. **Tag all resources**
7. **Document variables and outputs**
