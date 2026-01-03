# Documentation

This directory contains additional documentation for this Terraform module.

## API Documentation

Terraform modules are documented using [terraform-docs](https://terraform-docs.io/). 
The README.md in the module root is auto-generated.

### Generating Documentation

```bash
# Install terraform-docs
brew install terraform-docs  # macOS
# or
go install github.com/terraform-docs/terraform-docs@latest

# Generate README
terraform-docs markdown table . > README.md

# Or use the config file
terraform-docs -c .terraform-docs.yml .
```

### Configuration

Create `.terraform-docs.yml` in your module root:

```yaml
formatter: "markdown table"

version: ""

header-from: docs/header.md
footer-from: docs/footer.md

recursive:
  enabled: false

sections:
  hide: []
  show: []

content: ""

output:
  file: README.md
  mode: inject
  template: |-
    <!-- BEGIN_TF_DOCS -->
    {{ .Content }}
    <!-- END_TF_DOCS -->

output-values:
  enabled: false
  from: ""

sort:
  enabled: true
  by: name

settings:
  anchor: true
  color: true
  default: true
  description: true
  escape: true
  hide-empty: false
  html: true
  indent: 2
  lockfile: true
  read-comments: true
  required: true
  sensitive: true
  type: true
```

## Writing Good Documentation

### Variable Descriptions

```hcl
variable "instance_type" {
  description = "EC2 instance type for the web servers. Use t3.micro for dev, t3.medium for prod."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t3\\.(micro|small|medium|large)$", var.instance_type))
    error_message = "Instance type must be t3.micro, t3.small, t3.medium, or t3.large."
  }
}
```

### Output Descriptions

```hcl
output "endpoint" {
  description = "The HTTPS endpoint URL for the deployed API Gateway."
  value       = aws_apigateway_deployment.main.invoke_url
}
```

### Module Header

Create `docs/header.md`:

```markdown
# Module Name

Brief description of what this module does.

## Usage

\`\`\`hcl
module "example" {
  source  = "jbcom/example/aws"
  version = "1.0.0"

  name = "my-instance"
  environment = "production"
}
\`\`\`

## Features

- Feature 1
- Feature 2
- Feature 3
```

### Module Footer

Create `docs/footer.md`:

```markdown
## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Authors

- Jon Bogaty ([@jbcom](https://github.com/jbcom))
```

## jbcom Brand Guidelines

See the central [DESIGN-SYSTEM.md](../../always-sync/docs/DESIGN-SYSTEM.md) for:
- Color palette (for diagrams)
- Typography standards
- Accessibility requirements

For Terraform documentation, focus on:
- Clear, concise descriptions
- Practical usage examples
- Validation rules with helpful error messages

## Additional Resources

- [terraform-docs](https://terraform-docs.io/)
- [Terraform Module Documentation](https://developer.hashicorp.com/terraform/registry/modules/publish)
- [Terraform Registry](https://registry.terraform.io/)
