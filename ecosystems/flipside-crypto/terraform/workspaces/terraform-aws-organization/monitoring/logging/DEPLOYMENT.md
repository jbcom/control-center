# Taxonomy Website Deployment Plan

This document outlines the steps required to deploy the taxonomy website with Cognito authentication.

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Terraform installed
3. Node.js and npm installed (for Lambda function development)
4. SOPS installed (for managing encrypted secrets)
5. Google OAuth credentials (client ID and client secret)

## Pre-Deployment Steps

### 1. Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Create OAuth client ID credentials
   - Application type: Web application
   - Authorized JavaScript origins: `https://auth.[your-domain].auth.[region].amazoncognito.com`
   - Authorized redirect URIs: `https://auth.[your-domain].auth.[region].amazoncognito.com/oauth2/idpresponse`
5. Note the client ID and client secret

### 2. Create Encrypted Google OAuth Secrets File

Create an encrypted file with Google OAuth credentials:

```bash
# Create the secrets directory
mkdir -p secrets

# Create and encrypt the Google OAuth credentials file
cat > secrets/google.yaml << EOF
client_id: YOUR_GOOGLE_CLIENT_ID
client_secret: YOUR_GOOGLE_CLIENT_SECRET
EOF

# Encrypt the file with SOPS
sops --encrypt --aws-profile your-profile secrets/google.yaml > secrets/google.yaml.enc
mv secrets/google.yaml.enc secrets/google.yaml
```

### 3. Update Local Configuration

1. Update your `config.tf.json` file with the appropriate variables for your deployment:
   - Domain name
   - User pool group name
   - Admin email address

## Deployment Process

### 1. Initialize Terraform

```bash
terraform init
```

### 2. Verify the Terraform Plan

```bash
terraform plan
```

Review the plan to ensure that all resources will be created as expected.

### 3. Apply the Terraform Configuration

```bash
terraform apply
```

This will:
- Create the Cognito User Pool with Google OAuth integration
- Build and deploy the Lambda@Edge functions
- Create the CloudFront distribution
- Set up the S3 bucket for website content
- Configure DNS records

### 4. Verify the Deployment

After the deployment is complete:

1. Verify that the CloudFront distribution is properly configured
2. Check that the Cognito User Pool is created with Google OAuth integration
3. Verify that the Lambda@Edge functions are deployed and associated with CloudFront
4. Check that the S3 bucket is created and the website files are uploaded

## Post-Deployment Steps

### 1. Create Admin User

Create an admin user in the Cognito User Pool:

```bash
./scripts/create_test_user.sh \
  -e admin@example.com \
  -p StrongPassword123! \
  -g TaxonomyPortalUsers \
  -u $(terraform output -raw cognito_user_pool_id)
```

### 2. Test Authentication

1. Open the website URL in a browser
2. Verify that you are redirected to the Cognito login page
3. Sign in with the admin user credentials
4. Verify that you are redirected back to the website and can access protected content
5. Test Google OAuth login if configured

### 3. Monitor Logs

Check CloudWatch Logs for the Lambda@Edge functions to ensure they are functioning correctly.

## Troubleshooting

### CloudFront Distribution Issues

If the CloudFront distribution is not serving content correctly:

1. Check the origin configuration
2. Verify that the S3 bucket policy allows CloudFront access
3. Check the Lambda function associations

### Authentication Issues

If authentication is not working:

1. Check the Cognito User Pool configuration
2. Verify that Google OAuth is properly configured
3. Check the Lambda@Edge function logs in CloudWatch
4. Verify that the user is in the authorized group

### DNS Issues

If DNS resolution is not working:

1. Verify that the Route53 records are created
2. Check the ACM certificate status
3. Wait for DNS propagation (can take up to 48 hours)

## Cleanup

To clean up the deployment:

```bash
# Remove all resources
terraform destroy
```

Note that Lambda@Edge functions may remain in a "replicated" state for several hours after deletion. This is normal and they will eventually be removed. 