# AWS & Cloud Security Rules

## IAM Best Practices

### Required for All IAM Policies
- Follow least privilege principle
- Use conditions to restrict access
- Set explicit Deny for sensitive operations
- Include resource ARN restrictions
- Add IP or VPC endpoint conditions where applicable

### IAM Role Assumptions
```python
# ✅ Good - Explicit session name and duration
sts.assume_role(
    RoleArn='arn:aws:iam::123456789:role/MyRole',
    RoleSessionName='specific-session-name',
    DurationSeconds=3600
)

# ❌ Bad - No session tracking
sts.assume_role(RoleArn='...')
```

## S3 Security

### Required S3 Bucket Settings
- Encryption: AES256 or aws:kms
- Block Public Access: ALL enabled
- Versioning: Enabled for data protection
- Logging: Access logs to separate bucket
- SSL/TLS: Enforce via bucket policy

### Example Secure Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceSSL",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::bucket-name",
        "arn:aws:s3:::bucket-name/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

## DynamoDB Security

### Required Settings
- Encryption at rest: Enabled (KMS preferred)
- Point-in-time recovery: Enabled for production
- Streams encryption: Enabled if using streams

## SNS/SQS Security

### SNS Topics
- Encryption: aws:kms preferred
- Access policy: Restrict to specific principals
- Enforce HTTPS via policy

### SQS Queues
- Encryption at rest: Enabled
- Enforce HTTPS for all operations
- Set appropriate message retention

## Lambda Security

### Required Practices
- Use environment variables for config (encrypted)
- Attach minimal IAM role
- Enable VPC access only when needed
- Set appropriate timeout and memory
- Enable X-Ray tracing for observability

## Infrastructure as Code

### Terraform/CDK Requirements
- All resources must have tags:
  - `Environment` (dev/staging/prod)
  - `ManagedBy` (terraform/cdk)
  - `Owner` (team/project)
- State files must be encrypted
- Use remote state (S3 + DynamoDB locking)
- Plan before apply (CI/CD requirement)

## Secrets Management

### Required
- Use AWS Secrets Manager or SSM Parameter Store
- Rotate secrets regularly
- Audit secret access
- Use IAM for secret access control
- NEVER commit secrets to git

### Example
```python
# ✅ Good - Secrets Manager
import boto3
sm = boto3.client('secretsmanager')
secret = sm.get_secret_value(SecretId='my/secret')

# ❌ Bad - Hardcoded
API_KEY = "sk-1234567890abcdef"
```

## CloudWatch & Monitoring

### Required
- Enable CloudTrail for all regions
- Set up CloudWatch alarms for critical metrics
- Log all API calls
- Monitor failed login attempts
- Alert on privilege escalation

## Cost Optimization

### Check For
- Unused resources (EC2, EBS, EIPs)
- Over-provisioned instances
- Missing lifecycle policies (S3, ECR)
- Unattached EBS volumes
- Idle load balancers

## Compliance

### Must Review
- Data sovereignty requirements
- Encryption requirements
- Audit logging requirements
- Access control requirements
- Backup and disaster recovery requirements
