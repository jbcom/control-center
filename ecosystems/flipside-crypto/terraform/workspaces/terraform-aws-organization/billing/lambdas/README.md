# Billing Lambda Functions

This directory contains Lambda functions related to AWS billing and cost optimization:

## Billing Utilities Lambda

`billing_utilities.py` - A multi-purpose lambda function that handles:

1. **Billing Policy Migration** - Updates IAM policies with legacy `aws-portal:*` permissions to fine-grained billing permissions
2. **CUR Setup and Management** - Sets up and manages Cost and Usage Report buckets
3. **Cost Explorer Backfill** - Creates support tickets for backfilling Cost Explorer data
4. **Billing Conductor Operations** - Manages Billing Conductor configurations

The function can be invoked directly with specific operations or via CloudWatch scheduled events for regular maintenance. 