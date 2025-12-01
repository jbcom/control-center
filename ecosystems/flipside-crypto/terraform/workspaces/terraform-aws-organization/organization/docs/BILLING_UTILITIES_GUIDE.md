# AWS Billing Utilities Guide

This guide explains the AWS billing utilities implemented in this Terraform configuration, which includes automated billing policy migration, CUR management, and CUDOS integration.

## Overview

The AWS Billing Utilities solution addresses several key challenges:

1. **IAM Billing Policy Migration**: Automatically updates legacy `aws-portal:*` permissions to the new fine-grained IAM permissions model across your organization.

2. **Cost and Usage Report Management**: 
   - Creates and configures CUR buckets in each member account
   - Sets up replication to a central CUR bucket in the management account
   - Organizes data by account ID for proper organization-wide reporting

3. **CUDOS Integration**: Deploys AWS's Cloud Usage Dashboard for Obvious Savings solution for cost optimization.

## Architecture

The solution implements a multi-account architecture with targeted deployments:

### Management Account Components:
- Central CUR S3 bucket with organization-specific prefixes
- CUDOS CloudFormation stack deployment
- CloudFormation StackSet administration

### Resource OU Components (Deployments, Infrastructure, Isolated):
- Service-managed StackSet instances per OU
- Local CUR buckets with replication to central bucket
- IAM roles and policies for billing permissions
- Lambda functions for policy migration

### Testbed Account Components:
- Self-managed StackSet instances using ControlTower execution roles
- Direct account targeting for specialized environments
- Same billing utilities functionality as resource OUs

## Deployment Strategy

The solution uses a targeted deployment approach:

1. **OU-based Deployments**: For production resources in the Deployments, Infrastructure, and Isolated OUs
2. **Account-specific Deployments**: For testbed accounts, using direct account targeting
3. **CUDOS in Management Account**: A single CUDOS deployment in the management account

This strategy ensures that:
- Production environments have consistent billing utilities
- Testbed environments can be managed separately
- Resource-less OUs are not unnecessarily targeted

## Key Features

### 1. Billing Policy Migration
- Scans IAM policies across the organization for legacy billing permissions
- Automatically adds new fine-grained permissions alongside legacy permissions
- Provides extensive permission mappings for all billing-related services

### 2. CUR Management
- Creates standardized CUR configurations in member accounts
- Implements S3 replication with proper bucket policies
- Organizes data using the `organization/{org_id}/{account_id}/` path structure
- Configures proper encryption and lifecycle rules

### 3. CUDOS Deployment
- Deploys the official AWS CUDOS solution via CloudFormation
- Configures CUDOS to use the central CUR bucket
- Provides cost optimization dashboards with QuickSight

## Implementation Details

The solution uses a combination of deployment methods:

1. **Service-Managed StackSets**: For organizational units (using AWS Organizations integration)
2. **Self-Managed StackSets**: For specific accounts (using AWSControlTowerExecution roles)
3. **Direct CloudFormation Stack**: For CUDOS in the management account

## Usage

The billing utilities are automatically deployed as part of the AWS Organization Terraform configuration. No additional steps are required to enable them.

### Monitoring

The Lambda functions deployed to member accounts log all billing policy migration activities to CloudWatch Logs. You can monitor:

1. Policy scans and updates
2. CUR bucket configurations
3. S3 replication status

### Accessing CUDOS

Once deployed, CUDOS is available via Amazon QuickSight. You can access it using the URL:
```
https://{region}.quicksight.aws.amazon.com/sn/dashboards/cudos-dashboard
```

Replace `{region}` with your configured QuickSight region.

## Security Considerations

1. **IAM Permissions**: The solution uses least-privilege permissions models
2. **S3 Bucket Security**: CUR buckets are configured with:
   - Default encryption (AES256)
   - Proper access policies for the billing service
   - Lifecycle policies for data retention

3. **Organization Security**: All resources use organization-based conditions to restrict access

## Cost Considerations

This solution includes the following AWS resources that will incur costs:

- Lambda invocations (minimal)
- CloudWatch Logs (minimal)
- S3 storage for CUR data (varies by account usage)
- QuickSight for CUDOS dashboards

## Data Flow

1. AWS Cost and Usage Report data is delivered to each member account's S3
2. S3 replication copies the data to the central bucket in the management account
3. CUDOS reads and processes data from the central bucket
4. Reports are accessible via QuickSight dashboards

## Troubleshooting

### Common Issues

1. **S3 Replication Failures**:
   - Verify IAM roles have proper permissions
   - Check for any S3 bucket policy conflicts

2. **CUDOS Data Not Appearing**:
   - Verify the CUR data path structure is correct
   - Check that CloudFormation deployment completed successfully

3. **Policy Migration Issues**:
   - Examine CloudWatch Logs in the affected accounts
   - Verify the Lambda function has proper permissions

4. **StackSet Deployment Issues**:
   - For service-managed instances: Check Organizations integration permissions
   - For self-managed instances: Verify the AWSControlTowerExecution role exists and has correct permissions 