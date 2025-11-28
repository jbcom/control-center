# Vendor Connectors

Universal vendor connectors for the jbcom ecosystem, providing standardized access to cloud providers and third-party services.

## Features

- **AWS Connector**: Boto3-based client with role assumption and retry logic
- **Google Cloud Connector**: Workspace and Cloud Platform APIs with lazy credential loading
- **GitHub Connector**: Repository management, GraphQL queries, and file operations
- **Slack Connector**: Bot and app integrations with rate limiting
- **Vault Connector**: HashiCorp Vault with Token and AppRole auth
- **Zoom Connector**: Meeting and user management
- **VendorConnectors**: Cached public API with `get_*_client()` getters

## Installation

```bash
pip install vendor-connectors
```

## Usage

### Using VendorConnectors (Recommended)

The `VendorConnectors` class provides cached access to all connectors:

```python
from vendor_connectors import VendorConnectors

# Initialize once - reads credentials from environment
vc = VendorConnectors()

# Get cached clients
slack = vc.get_slack_client()
github = vc.get_github_client(github_owner="myorg")
s3 = vc.get_aws_client("s3")
vault = vc.get_vault_client()
```

### Using Individual Connectors

```python
from vendor_connectors import AWSConnector, GithubConnector, SlackConnector

# AWS with role assumption
aws = AWSConnector(execution_role_arn="arn:aws:iam::123456789012:role/MyRole")
s3 = aws.get_aws_client("s3")

# GitHub operations
github = GithubConnector(
    github_owner="myorg",
    github_repo="myrepo",
    github_token=os.getenv("GITHUB_TOKEN")
)

# Slack messaging
slack = SlackConnector(
    token=os.getenv("SLACK_TOKEN"),
    bot_token=os.getenv("SLACK_BOT_TOKEN")
)
slack.send_message("general", "Hello from vendor-connectors!")
```

## Architecture

All connectors extend `DirectedInputsClass` from the jbcom ecosystem:

- **directed-inputs-class**: Input handling from environment, stdin, config
- **lifecyclelogging**: Structured logging with verbosity control
- **extended-data-types**: Utilities like `is_nothing`, `strtobool`, `wrap_raw_data_for_export`

The `VendorConnectors` class provides:
- Client caching (same parameters = same instance)
- Automatic credential loading from environment
- Consistent interface across all providers

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AWS_*` | Standard AWS credentials |
| `EXECUTION_ROLE_ARN` | AWS role to assume |
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITHUB_OWNER` | GitHub organization/user |
| `GOOGLE_SERVICE_ACCOUNT` | Google service account JSON |
| `SLACK_TOKEN` | Slack user token |
| `SLACK_BOT_TOKEN` | Slack bot token |
| `VAULT_ADDR` | Vault server URL |
| `VAULT_TOKEN` | Vault authentication token |
| `VAULT_ROLE_ID` / `VAULT_SECRET_ID` | AppRole credentials |
| `ZOOM_CLIENT_ID` / `ZOOM_CLIENT_SECRET` / `ZOOM_ACCOUNT_ID` | Zoom OAuth |

## Part of jbcom Ecosystem

This package is part of the jbcom Python library ecosystem:
- [extended-data-types](https://pypi.org/project/extended-data-types/) - Foundation utilities
- [lifecyclelogging](https://pypi.org/project/lifecyclelogging/) - Structured logging
- [directed-inputs-class](https://pypi.org/project/directed-inputs-class/) - Input handling


