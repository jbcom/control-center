# Guards Workspace

This workspace manages guard lambdas that help govern the management account for the AWS organization. Guard lambdas extend beyond what Service Control Policies (SCPs) can do by providing active monitoring and remediation capabilities.

## New Architecture (Configuration-Driven)

Guards are now configured via YAML files in `config/guards/` and deployed automatically using a for_each pattern. This provides:

- **Configuration as Code**: All guard settings in version-controlled YAML
- **Automatic Deployment**: Guards are deployed based on config files
- **Centralized Source**: Lambda source code in `src/guards/` at repository root
- **Simplified Management**: Add new guards by creating config files

## Lambda Requirements

All guard lambdas in this workspace must follow these requirements:

### Runtime and Language
- **Runtime**: provided.al2023 (for Go)
- **Language**: Go 1.21+
- **Architecture**: ARM64 for cost efficiency
- **Build**: Cross-compiled for Linux ARM64

### Code Structure
- **Source Location**: `src/guards/{guard-name}/` at repository root
- **Configuration**: `config/guards/{guard-name}.yaml`
- **Main Handler**: `main.go` with bootstrap binary output
- **Dependencies**: `go.mod` and `go.sum` for dependency management
- **Tests**: `*_test.go` files alongside source code

### Dependencies
- Use AWS SDK for Go v2 (`github.com/aws/aws-sdk-go-v2`)
- Use AWS Lambda Go runtime (`github.com/aws/aws-lambda-go`)
- Minimize external dependencies
- Use `testify` for testing framework

## Configuration Structure

Each guard is configured via a YAML file in `config/guards/{guard-name}.yaml`:

```yaml
# Build configuration
build:
  artifacts_dir: "builds/guards"
  attach_tracing_policy: false

# Deploy configuration  
deploy:
  config_name: "CodeDeployDefault.Lambda10PercentEvery5Minutes"
  force_deploy: false
  save_deploy_script: true
  wait_deployment_completion: true
  auto_rollback_enabled: true
  auto_rollback_events:
    - "DEPLOYMENT_FAILURE"
    - "DEPLOYMENT_STOP_ON_ALARM"

# Monitoring configuration
monitoring:
  cloudwatch_logs_retention_days: 30
  cloudwatch_logs_log_group_class: "STANDARD"
  maximum_retry_attempts: 2
  maximum_event_age_in_seconds: 3600
  dlq_message_retention_seconds: 1209600

# Performance configuration
performance:
  reserved_concurrent_executions: 1

# Lambda configuration
lambda:
  description: "Guard lambda description"
  handler: "bootstrap"
  runtime: "provided.al2023"
  architectures:
    - "arm64"
  timeout: 300
  memory_size: 512

# Schedule configuration
schedule:
  expression: "rate(1 day)"
  description: "Schedule description"

# Environment variables
environment:
  LOG_LEVEL: "INFO"
  DRY_RUN: "false"

# IAM policy statements
policy_statements:
  read_policy:
    effect: "Allow"
    actions:
      - "service:ListResources"
    resources:
      - "*"

# Guard-specific tags
tags:
  GuardType: "Example"
  Schedule: "Daily"
```

## Current Guards

### IAM User Cleanup Guard (`iam-user-cleanup`)

**Purpose**: Manages inactive IAM users in the management account with progressive cleanup.

**Configuration**: `config/guards/iam-user-cleanup.yaml`
**Source Code**: `src/guards/iam-user-cleanup/`

**Schedule**: Daily execution

**Functionality**:
- 90+ days inactive: Disable access keys
- 180+ days inactive: Disable user (remove login profile + disable keys)
- 270+ days inactive: Delete user completely

**Admin Bot Protection**: Uses `local.context.admin_bot_users` allowlist to protect essential service accounts.

**Environment Variables**:
- `ADMIN_BOT_USERS`: JSON-encoded array of admin principal ARNs (automatically set)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DRY_RUN`: Set to "true" for testing without making changes (default: false)
- `DAYS_TO_DISABLE_KEYS`: Days before disabling keys (default: 90)
- `DAYS_TO_DISABLE_USER`: Days before disabling user (default: 180)
- `DAYS_TO_DELETE_USER`: Days before deleting user (default: 270)

## Module Architecture

Guards use the `aws-guard-lambda-deployment` module which provides:

- **Lambda Function**: With proper IAM roles, logging, and error handling
- **EventBridge Scheduling**: Configurable cron/rate expressions
- **Lambda Alias**: For version management and controlled deployments
- **CodeDeploy Integration**: Gradual rollout with notifications
- **Dead Letter Queue**: Error handling and monitoring
- **CloudWatch Alarms**: Monitoring for failed executions
- **SNS Topics**: Deployment notifications

The module is organized across multiple files:
- `build.tf`: Lambda function and EventBridge scheduling
- `deploy.tf`: CodeDeploy, aliases, and deployment notifications
- `monitoring.tf`: Dead letter queues and CloudWatch alarms
- `locals.tf`: Configuration extraction and defaults

## Adding New Guards

To add a new guard lambda:

1. **Create Source Code**: Add directory `src/guards/{guard-name}/`
2. **Add Lambda Code**: Create `main.go` with your Go lambda code
3. **Add Dependencies**: Create `go.mod` with required dependencies
4. **Add Tests**: Create comprehensive tests in `main_test.go`
5. **Create Configuration**: Add `config/guards/{guard-name}.yaml`
6. **Deploy**: Guards are automatically deployed via for_each

Example structure:
```
src/guards/
├── iam-user-cleanup/
│   ├── main.go
│   ├── main_test.go
│   ├── go.mod
│   └── go.sum
└── new-guard/
    ├── main.go
    ├── main_test.go
    ├── go.mod
    └── go.sum

config/guards/
├── iam-user-cleanup.yaml
└── new-guard.yaml
```

## Workspace Structure

The workspace is now extremely simple:

```hcl
# Deploy all guards defined in config/guards/
module "guards" {
  for_each = local.context.guards
  
  source = "../../modules/aws-guard-lambda-deployment"

  # CloudPosse context and guard name
  context = local.context
  name    = each.key
}
```

This automatically deploys all guards configured in `config/guards/` directory.

## Security Considerations

- All guards respect the `local.context.admin_bot_users` allowlist
- Guards use least-privilege IAM policies
- DRY_RUN mode available for testing
- Comprehensive logging for audit trails
- Progressive actions (warn → disable → delete) for safety

## Monitoring

Each guard includes:
- CloudWatch Logs with configurable retention
- Dead Letter Queue for failed executions
- CloudWatch Alarms for monitoring failures
- SNS notifications for deployment events

## Testing Strategy

Guards require comprehensive testing to ensure they operate safely in production.

### Testing Approach

**Go Testing Conventions**
- Use standard Go testing with `*_test.go` files
- Use `testify/assert` for assertions
- Use `testify/mock` for mocking AWS services
- Test files alongside source code for easy maintenance

**Testing Priorities**
1. **Unit Tests**: Fast feedback for business logic
2. **Integration Tests**: Test with real AWS services in isolated environment
3. **End-to-End Tests**: Complete workflow validation

### Running Tests
```bash
# Run all tests for a guard
cd src/guards/iam-user-cleanup
go test -v

# Run tests with coverage
go test -v -cover

# Run specific test
go test -v -run TestGetUserLastActivity

# Run tests with race detection
go test -v -race
```

### Build Testing
```bash
# Test Go build for Lambda
cd src/guards/iam-user-cleanup
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bootstrap main.go

# Verify binary
file bootstrap
# Should output: bootstrap: ELF 64-bit LSB executable, ARM aarch64
```

### Deployment Testing
```bash
# Plan deployment
cd workspaces/guards
terraform plan

# Apply in test environment
terraform apply

# Test lambda execution
aws lambda invoke --function-name {guard-name}-guard response.json
cat response.json
```

## Configuration Management

### Guard Configuration Processing

The module automatically:
1. Extracts configuration from `var.context.guards[var.name]`
2. Applies sensible defaults using Terraform's `defaults()` function
3. Injects `ADMIN_BOT_USERS` environment variable automatically
4. Constructs source path using `rel_to_root` and `base_src_dir`
5. Processes IAM policy conditions to include admin bot users

### Source Path Construction

Source paths are automatically constructed as:
```
${local.rel_to_root}/${local.base_src_dir}/${var.name}
```

Where:
- `rel_to_root`: `../..` (from workspace to repository root)
- `base_src_dir`: `src/guards`
- `var.name`: The guard name (e.g., `iam-user-cleanup`)

Result: `../../src/guards/iam-user-cleanup`

### Admin Bot Users Integration

The module automatically:
- Injects `ADMIN_BOT_USERS` environment variable with JSON-encoded allowlist
- Updates IAM policy conditions to include admin bot users in `values`
- Ensures all guards respect the organization's admin allowlist

## Benefits of New Architecture

1. **Simplified Deployment**: Just add a YAML file to deploy a new guard
2. **Consistent Configuration**: All guards follow the same configuration pattern
3. **Centralized Source**: Lambda code organized at repository root
4. **Automatic Integration**: Admin bot users and context automatically injected
5. **Modular Design**: Module split into logical files for maintainability
6. **CI/CD Optimized**: Package handling optimized for clean CI/CD environments

This architecture makes it extremely easy to add new guards while maintaining consistency and security across all deployments.
