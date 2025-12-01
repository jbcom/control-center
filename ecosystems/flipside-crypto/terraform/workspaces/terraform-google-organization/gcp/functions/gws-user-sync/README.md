# Google Workspace User Sync Cloud Function (Scheduled)

This Go-based Google Cloud Function synchronizes Google Workspace users and groups for FlipsideCrypto on a scheduled basis. It's a port of the Python functionality focusing specifically on Google Cloud/Google Workspace operations.

## Features

- **Scheduled Execution**: Runs automatically on a configurable schedule (default: weekdays at 9 AM UTC)
- **User Management**: Processes Google Workspace users based on their organizational unit and status
- **User Classification**: Categorizes users as active, inactive, or bot users
- **Organizational Unit Handling**: Manages users across different OUs (Users, Consultants, Automation, LimitedAccess)
- **Team Calendar Integration**: Manages access to the team calendar
- **Group Management**: Handles Google Workspace group memberships
- **Custom Schema Management**: Manages vendor attributes in user profiles
- **AWS Identity Center Integration**: Synchronizes Google Workspace groups to AWS Identity Center
- **Comprehensive Logging**: Uses Google Cloud Logging for monitoring and debugging

## Architecture

The function is split into multiple files for maintainability:

- `main.go`: Cloud Event handler and entry point for scheduled execution
- `sync_service.go`: Core synchronization logic
- `logger.go`: Cloud Logging wrapper
- `types.go`: Type definitions and constants
- `go.mod`: Go module dependencies

## User Processing Logic

### User Types
- **Active**: Regular users in `/Users` or other standard OUs
- **Inactive**: Suspended or archived users
- **Bot**: Users in `/Automation` organizational unit

### User Lifecycle
1. **Active Users**: Added to team group and calendar (except consultants)
2. **Consultants**: Removed from team resources but remain active
3. **Inactive Users**: Moved to `/LimitedAccess` and archived, removed from team resources

## Scheduling

### Default Schedule
- **Frequency**: Monday through Friday at 9:00 AM UTC
- **Cron Expression**: `0 9 * * 1-5`
- **Timezone**: UTC

### Manual Triggering
You can manually trigger the function using:
```bash
gcloud pubsub topics publish gws-user-sync-trigger --message='{"trigger":"manual"}'
```

### Monitoring
View function execution logs:
```bash
gcloud functions logs read gws-user-sync --region=us-central1
```

## Configuration

### Environment Variables

#### Required (Google Workspace)
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (defaults to "flipsidecrypto")

#### Optional (AWS Identity Center Integration)
- `AWS_ACCESS_KEY_ID`: AWS access key for Identity Center access
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key for Identity Center access
- `AWS_REGION`: AWS region (defaults to "us-east-1")
- `AWS_PROFILE`: Alternative to access keys, AWS profile name

**Note**: AWS integration is optional. If AWS credentials are not provided, the function will skip AWS synchronization and only perform Google Workspace operations.

### Required Scopes
- `https://www.googleapis.com/auth/admin.directory.user`
- `https://www.googleapis.com/auth/admin.directory.group`
- `https://www.googleapis.com/auth/admin.directory.orgunit`
- `https://www.googleapis.com/auth/admin.directory.user.schema`
- `https://www.googleapis.com/auth/calendar`

## Deployment

This function is designed to be deployed as a Google Cloud Function with the following characteristics:

- **Runtime**: Go 1.21
- **Trigger**: Pub/Sub (scheduled via Cloud Scheduler)
- **Authentication**: Service account with appropriate Google Workspace admin permissions
- **Memory**: 512MB (adjustable based on user count)
- **Timeout**: 540 seconds (9 minutes)

### Deployment Process

The function uses an automated deployment script that:

1. **Creates Pub/Sub Topic**: Creates `gws-user-sync-trigger` topic for triggering the function
2. **Deploys Cloud Function**: Deploys the function with Pub/Sub trigger
3. **Sets Up Scheduler**: Creates a Cloud Scheduler job to publish messages on schedule
4. **Configures Schedule**: Default schedule runs Monday-Friday at 9 AM UTC

To deploy:
```bash
cd workspaces/gcp/functions/gws-user-sync
./deploy.sh
```

## Dependencies

- Google Cloud Functions Framework
- Google Admin SDK
- Google Calendar API
- Google Cloud Logging
- AWS SDK v2 (Identity Store and SSO Admin services)

## Security

- Uses service account authentication
- Requires domain-wide delegation for Google Workspace APIs
- Implements proper error handling and logging
- No sensitive data stored in code

## Monitoring

- All operations logged to Google Cloud Logging
- Error tracking through structured logging
- Success/failure metrics available in function logs

## AWS Identity Center Integration

When AWS credentials are provided, the function will automatically:

1. **Discover AWS SSO Configuration**: Automatically finds the SSO Instance ARN and Identity Store ID
2. **Sync Google Groups**: Creates corresponding groups in AWS Identity Center
3. **Manage Group Membership**: Synchronizes user memberships between Google Workspace and AWS
4. **Domain Filtering**: Only syncs users from @flipsidecrypto.com domain
5. **Safe Operations**: Never automatically removes entire groups, only manages individual memberships

### AWS Permissions Required

The AWS credentials must have permissions for:
- `identitystore:ListGroups`
- `identitystore:CreateGroup`
- `identitystore:ListUsers`
- `identitystore:ListGroupMemberships`
- `identitystore:CreateGroupMembership`
- `identitystore:DeleteGroupMembership`
- `sso:ListInstances`

## Excluded Functionality

This implementation focuses on Google Cloud/Google Workspace operations with optional AWS Identity Center integration. The following vendor integrations from the original Python code are intentionally excluded:

- AWS account provisioning (only group sync is included)
- Zoom user management
- Slack integrations
- GitHub user synchronization
- Gemini license management

These exclusions keep the function focused and reduce complexity while maintaining the core synchronization functionality.
