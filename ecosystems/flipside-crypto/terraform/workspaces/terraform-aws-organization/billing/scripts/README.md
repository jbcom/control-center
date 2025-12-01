# Billing-Related Scripts

This directory contains utility scripts for billing and cost optimization:

## Lambda Package Creation

`create_lambda_package.sh` - Creates a Lambda deployment package for the QuickSight setup Lambda function:

- Creates a Node.js project with necessary dependencies
- Packages the Lambda code with required node modules
- Creates a zip file ready for Lambda deployment

This script primarily supports CUDOS dashboard creation and QuickSight resources management. 