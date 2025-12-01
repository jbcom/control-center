# AWS Billing Configuration

This directory contains the configuration files for AWS billing and cost management resources managed by the billing pipeline.

## Configuration Files

- **services.yaml** - Defines all billing-related services including Cost Explorer, Cost Optimization, CUR, and billing conductor settings
- **budgets.yaml** - Configures budgets at organization, OU, and account levels
- **cost_allocation_tags.yaml** - Sets up cost allocation tags for better cost tracking

## Integration with Main Organization

This billing pipeline is a downstream dependency of the main AWS organization pipeline. It relies on outputs from the main pipeline including:

- Organization structure and IDs
- Account information
- OU structure

## Configuration Structure

The configuration is designed to be flat and intuitive since this is a billing-specific pipeline. Each file focuses on a specific aspect of billing and cost management:

1. **Services** - All AWS billing services configuration
2. **Budgets** - Budget definitions and notification settings
3. **Cost Allocation Tags** - Tag structure for cost attribution

## Usage

To modify the billing configuration:

1. Edit the appropriate YAML file in this directory
2. Commit and push changes
3. The CI/CD pipeline will apply the changes to the AWS environment

## Dependencies

The billing pipeline depends on:
- AWS Organization structure (from main pipeline)
- Account configurations (from accounts workspace)
- Unit configurations (from units workspace)

For more details on the specific resources managed by this pipeline, refer to the Terraform files in the parent directory. 