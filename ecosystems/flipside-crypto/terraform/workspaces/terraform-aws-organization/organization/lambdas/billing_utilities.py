"""
Billing Utilities Lambda Function

This Lambda function consolidates multiple billing-related operations:
1. Billing policy migration for IAM policies (legacy aws-portal:* to fine-grained permissions)
2. CUR bucket setup and management
3. Support ticket creation for backfilling Cost Explorer data

The function can be invoked directly or via CloudWatch scheduled events.
"""

import json
import os
import boto3
import logging
from datetime import datetime, timedelta
import uuid
import time
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
MANAGEMENT_ACCOUNT_ID = os.environ.get('MANAGEMENT_ACCOUNT_ID')
ENABLE_AUTO_UPDATES = os.environ.get('ENABLE_AUTO_UPDATES', 'false').lower() == 'true'
MIGRATION_ROLE_NAME = os.environ.get('MIGRATION_ROLE_NAME', 'BillingConsolePolicyMigratorRole')
INCLUDE_BILLING_CONDUCTOR = os.environ.get('INCLUDE_BILLING_CONDUCTOR', 'true').lower() == 'true'
INCLUDE_CUR = os.environ.get('INCLUDE_CUR', 'true').lower() == 'true'
ORGANIZATION_ID = os.environ.get('ORGANIZATION_ID')
CUR_BUCKET_PREFIX = os.environ.get('CUR_BUCKET_PREFIX', 'fsc-cur')

# Constants
MAX_RETRIES = 3
RETRY_DELAY_MS = 1000

# AWS Service mapping for old portal actions to new fine-grained actions
ACTION_MAPPING = {
    'aws-portal:ViewBilling': [
        'account:GetAccountInformation',
        'billing:GetBillingData',
        'billing:GetBillingDetails',
        'billing:GetBillingPreferences',
        'billing:GetPaymentMethods',
        'ce:ListCostCategoryDefinitions',
        'ce:DescribeCostCategoryDefinition',
        'consolidatedbilling:GetAccountBillingRole',
        'consolidatedbilling:ListLinkedAccounts',
        'cur:GetClassicReport',
        'cur:GetClassicReportPreferences',
        'freetier:GetFreeTierAlertPreference',
        'freetier:GetFreeTierUsage',
        'invoicing:GetInvoiceEmailDeliveryPreferences',
        'invoicing:GetInvoicePDF',
        'invoicing:ListInvoiceSummaries',
        'payments:GetPaymentInstrument',
        'payments:ListPaymentInstruments',
        'payments:ListPaymentPreferences',
        'tax:GetTaxInheritance',
        'tax:GetTaxRegistrationDocument',
        'tax:ListTaxRegistrations'
    ],
    'aws-portal:ViewUsage': [
        'ce:GetCostAndUsage',
        'ce:GetCostAndUsageWithResources',
        'ce:GetCostForecast',
        'ce:GetDimensionValues',
        'ce:GetReservationUtilization',
        'ce:GetSavingsPlansUtilization',
        'ce:GetUsageForecast'
    ],
    'aws-portal:ViewAccount': [
        'account:GetAccountInformation',
        'account:GetAlternateContact',
        'account:GetChallengeQuestions',
        'account:GetContactInformation',
        'billing:GetIAMAccessPreference',
        'billing:GetSellerOfRecord',
        'payments:GetPaymentStatus'
    ],
    'aws-portal:ModifyBilling': [
        'billing:UpdateBillingPreferences',
        'consolidatedbilling:ListLinkedAccounts',
        'cur:ModifyClassicReport',
        'cur:ModifyClassicReportPreferences',
        'cur:PutClassicReportPreferences',
        'freetier:PutFreeTierAlertPreference',
        'invoicing:PutInvoiceEmailDeliveryPreferences',
        'payments:UpdatePaymentPreferences',
        'tax:BatchPutTaxRegistration',
        'tax:DeleteTaxRegistration',
        'tax:PutTaxInheritance',
        'tax:PutTaxRegistration'
    ],
    'aws-portal:ModifyAccount': [
        'account:PutAlternateContact',
        'account:PutChallengeQuestions',
        'account:PutContactInformation',
        'billing:PutIAMAccessPreference',
        'billing:UpdateSellerOfRecord'
    ],
    'aws-portal:ModifyPaymentMethods': [
        'payments:DeletePaymentInstrument',
        'payments:MakePayment',
        'payments:PutPaymentInstrument',
        'payments:UpdatePaymentPreferences'
    ]
}

# Additional Billing Conductor permissions mapping
BILLING_CONDUCTOR_MAPPING = {
    'aws-portal:ViewBilling': [
        'billingconductor:ListAccountAssociations',
        'billingconductor:ListBillingGroups',
        'billingconductor:GetBillingGroupCostReport',
        'billingconductor:ListPricingPlans',
        'billingconductor:ListPricingRules',
        'billingconductor:GetPricingPlan',
        'billingconductor:GetPricingRule'
    ],
    'aws-portal:ModifyBilling': [
        'billingconductor:AssociateAccounts',
        'billingconductor:DisassociateAccounts',
        'billingconductor:CreateBillingGroup',
        'billingconductor:DeleteBillingGroup',
        'billingconductor:UpdateBillingGroup',
        'billingconductor:CreatePricingPlan',
        'billingconductor:UpdatePricingPlan',
        'billingconductor:DeletePricingPlan',
        'billingconductor:CreatePricingRule',
        'billingconductor:UpdatePricingRule',
        'billingconductor:DeletePricingRule',
        'billingconductor:CreateCustomLineItem',
        'billingconductor:UpdateCustomLineItem',
        'billingconductor:DeleteCustomLineItem'
    ]
}

# Additional CUR permissions mapping
CUR_MAPPING = {
    'aws-portal:ViewBilling': [
        'cur:GetUsageReport',
        'cur:DescribeReportDefinitions',
        'cur:GetClassicReport',
        'cur:GetUsageReportSubscriptions'
    ],
    'aws-portal:ModifyBilling': [
        'cur:PutReportDefinition',
        'cur:DeleteReportDefinition',
        'cur:ModifyReportDefinition'
    ]
}

def handler(event, context):
    """Main Lambda handler function"""
    
    # Get account ID from the Lambda context
    try:
        account_id = context.invoked_function_arn.split(":")[4]
        logger.info(f'Function invoked in account {account_id}')
        
        # Determine if this is an event-driven invocation with operation
        if isinstance(event, dict) and 'operation' in event:
            # Handle operation-based invocation for support utilities
            return handle_operation(event, account_id)
        
        # Default to billing policy migration
        results = {}
        
        # Handle billing policy migration
        policy_results = handle_policy_migration(account_id)
        results.update(policy_results)
        
        # Handle CUR bucket setup if enabled
        if INCLUDE_CUR:
            cur_results = handle_cur_setup(account_id)
            results.update(cur_results)
        
        # Return combined results
        return {
            'statusCode': 200,
            'body': results
        }
        
    except Exception as e:
        logger.error(f'Error in Lambda handler: {str(e)}')
        raise

def handle_operation(event, account_id):
    """Handle operation-specific invocations"""
    operation = event.get('operation')
    logger.info(f'Handling operation: {operation}')
    
    try:
        if operation == 'CREATE_SUPPORT_TICKET':
            return create_support_ticket(event)
        elif operation == 'CREATE_BACKFILL_TICKET':
            return create_backfill_ticket(event, account_id)
        elif operation == 'GET_SUPPORT_TICKET':
            return get_support_ticket(event)
        elif operation == 'NOTIFY_MANAGEMENT_ACCOUNT':
            return notify_management_account(event)
        elif operation == 'MANUAL_POLICY_SCAN':
            return handle_policy_migration(account_id, force_scan=True)
        elif operation == 'SETUP_CUR_BUCKET':
            return handle_cur_setup(account_id, force_setup=True)
        else:
            raise ValueError(f'Unsupported operation: {operation}')
    except Exception as e:
        logger.error(f'Error processing {operation}: {str(e)}')
        raise

def handle_policy_migration(account_id, force_scan=False):
    """Handle billing policy migration"""
    try:
        logger.info(f'Running billing policy migration in account {account_id}')
        
        # Get all IAM policies in the account
        iam_client = boto3.client('iam')
        affected_policies = find_affected_policies(iam_client)
        
        logger.info(f'Found {len(affected_policies)} affected policies')
        
        # Process policies
        if ENABLE_AUTO_UPDATES or force_scan:
            update_policies(iam_client, affected_policies)
        else:
            logger.info('Auto-updates disabled. Running in scan-only mode')
            for policy_name, policy_data in affected_policies.items():
                logger.info(f'Policy {policy_name} needs updates: {policy_data["needs_updates"]}')
                if policy_data["needs_updates"]:
                    logger.info(f'Old actions: {policy_data["old_actions"]}')
                    logger.info(f'Suggested new actions: {policy_data["new_actions"]}')
        
        # Check for Billing Conductor configurations
        bc_configs = None
        if INCLUDE_BILLING_CONDUCTOR:
            bc_configs = check_billing_conductor_config()
        
        return {
            'account_id': account_id,
            'affected_policies_count': len(affected_policies),
            'scan_time': datetime.now().isoformat(),
            'auto_updates_enabled': ENABLE_AUTO_UPDATES,
            'include_cur': INCLUDE_CUR,
            'include_billing_conductor': INCLUDE_BILLING_CONDUCTOR,
            'billing_conductor_configs': bc_configs
        }
    except Exception as e:
        logger.error(f'Error in billing policy migration: {str(e)}')
        raise

def handle_cur_setup(account_id, force_setup=False):
    """Handle CUR bucket setup"""
    try:
        logger.info(f'Checking CUR setup for account {account_id}')
        
        # Check existing CUR configurations
        cur_definitions = check_cur_config()
        
        # Create bucket if needed
        bucket_info = setup_cur_bucket(account_id, force_setup)
        
        # Check if we need to create support ticket for backfill
        backfill_needed = len(cur_definitions) == 0 or force_setup
        backfill_ticket = None
        
        if backfill_needed:
            try:
                backfill_event = {
                    'accountId': account_id,
                    'organizationId': ORGANIZATION_ID,
                    'curBucketName': bucket_info['bucket_name'],
                    'backfillMonths': 38  # Request maximum historical data
                }
                backfill_ticket = create_backfill_ticket(backfill_event, account_id)
                logger.info(f'Created backfill ticket: {backfill_ticket}')
            except Exception as e:
                logger.error(f'Error creating backfill ticket: {str(e)}')
                # Continue even if backfill ticket fails
        
        return {
            'cur_bucket': bucket_info,
            'cur_definitions': cur_definitions,
            'backfill_ticket': backfill_ticket
        }
    except Exception as e:
        logger.error(f'Error in CUR setup: {str(e)}')
        raise

def setup_cur_bucket(account_id, force_setup=False):
    """Set up CUR bucket for the account"""
    bucket_name = f"{CUR_BUCKET_PREFIX}-{account_id}"
    s3_client = boto3.client('s3')
    
    try:
        # Check if bucket already exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f'CUR bucket {bucket_name} already exists')
            bucket_exists = True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                bucket_exists = False
            else:
                # Other error, re-raise
                raise
        
        # Create bucket if it doesn't exist or force_setup is True
        if not bucket_exists or force_setup:
            region = boto3.session.Session().region_name
            logger.info(f'Creating CUR bucket {bucket_name} in {region}')
            
            # Create the bucket
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Set up bucket policy for CUR
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {'Service': 'billingreports.amazonaws.com'},
                        'Action': [
                            's3:GetBucketAcl',
                            's3:GetBucketPolicy'
                        ],
                        'Resource': f'arn:aws:s3:::{bucket_name}'
                    },
                    {
                        'Effect': 'Allow',
                        'Principal': {'Service': 'billingreports.amazonaws.com'},
                        'Action': 's3:PutObject',
                        'Resource': f'arn:aws:s3:::{bucket_name}/*'
                    }
                ]
            }
            
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Set up default encryption
            s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            # Set up lifecycle policy
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'AutoExpire',
                        'Status': 'Enabled',
                        'Expiration': {
                            'Days': 1825  # 5 years retention
                        },
                        'Filter': {
                            'Prefix': ''
                        }
                    }
                ]
            }
            
            s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            logger.info(f'Successfully created and configured CUR bucket {bucket_name}')
        
        # Set up CUR report definition if it doesn't exist
        cur_client = boto3.client('cur')
        report_definitions = cur_client.describe_report_definitions()
        report_name = f'cur-{account_id}'
        
        # Check if CUR definition exists
        cur_exists = any(rd['ReportName'] == report_name for rd in report_definitions.get('ReportDefinitions', []))
        
        if not cur_exists or force_setup:
            logger.info(f'Creating CUR definition {report_name}')
            
            # Create CUR definition
            cur_client.put_report_definition(
                ReportDefinition={
                    'ReportName': report_name,
                    'TimeUnit': 'HOURLY',
                    'Format': 'Parquet',
                    'Compression': 'Parquet',
                    'AdditionalSchemaElements': [
                        'RESOURCES',
                        'SPLIT_COST_ALLOCATION_DATA'
                    ],
                    'S3Bucket': bucket_name,
                    'S3Prefix': 'reports',
                    'S3Region': region,
                    'RefreshClosedReports': True,
                    'ReportVersioning': 'OVERWRITE_REPORT'
                }
            )
            
            logger.info(f'Successfully created CUR definition {report_name}')
        
        return {
            'bucket_name': bucket_name,
            'report_name': report_name,
            'new_bucket_created': not bucket_exists or force_setup,
            'new_report_created': not cur_exists or force_setup
        }
        
    except Exception as e:
        logger.error(f'Error setting up CUR bucket {bucket_name}: {str(e)}')
        raise

def check_cur_config():
    """Check existing CUR configurations and log information about them"""
    try:
        cur_client = boto3.client('cur')
        report_definitions = cur_client.describe_report_definitions()
        
        logger.info(f'Found {len(report_definitions.get("ReportDefinitions", []))} CUR report definitions')
        
        report_info = []
        for report in report_definitions.get('ReportDefinitions', []):
            report_data = {
                'ReportName': report.get('ReportName'),
                'S3Bucket': report.get('S3Bucket'),
                'S3Prefix': report.get('S3Prefix'),
                'TimeUnit': report.get('TimeUnit'),
                'Format': report.get('Format')
            }
            logger.info(f'CUR Report: {report.get("ReportName")} - S3 Bucket: {report.get("S3Bucket")}')
            report_info.append(report_data)
            
        return report_info
    except Exception as e:
        logger.warning(f'Unable to check CUR configurations: {str(e)}')
        return []

def check_billing_conductor_config():
    """Check existing Billing Conductor configurations and log information about them"""
    try:
        bc_client = boto3.client('billingconductor')
        
        # Check billing groups
        billing_groups = bc_client.list_billing_groups().get('BillingGroups', [])
        logger.info(f'Found {len(billing_groups)} Billing Conductor billing groups')
        
        # Check pricing plans
        pricing_plans = bc_client.list_pricing_plans().get('PricingPlans', [])
        logger.info(f'Found {len(pricing_plans)} Billing Conductor pricing plans')
        
        # Check pricing rules
        pricing_rules = bc_client.list_pricing_rules().get('PricingRules', [])
        logger.info(f'Found {len(pricing_rules)} Billing Conductor pricing rules')
        
        return {
            'billing_groups': len(billing_groups),
            'pricing_plans': len(pricing_plans),
            'pricing_rules': len(pricing_rules)
        }
    except Exception as e:
        logger.warning(f'Unable to check Billing Conductor configurations: {str(e)}')
        return None
    
def find_affected_policies(iam_client):
    affected_policies = {}
    
    # Get customer managed policies
    paginator = iam_client.get_paginator('list_policies')
    for page in paginator.paginate(Scope='Local'):
        for policy in page['Policies']:
            policy_details = iam_client.get_policy(PolicyArn=policy['Arn'])
            policy_version = iam_client.get_policy_version(
                PolicyArn=policy['Arn'],
                VersionId=policy_details['Policy']['DefaultVersionId']
            )
            document = policy_version['PolicyVersion']['Document']
            
            analyze_policy(policy['PolicyName'], document, 'managed', policy['Arn'], affected_policies)
    
    # Get inline policies for roles
    paginator = iam_client.get_paginator('list_roles')
    for page in paginator.paginate():
        for role in page['Roles']:
            role_name = role['RoleName']
            try:
                # List inline policies for the role
                inline_policies = iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
                for policy_name in inline_policies:
                    try:
                        policy_document = iam_client.get_role_policy(
                            RoleName=role_name,
                            PolicyName=policy_name
                        )['PolicyDocument']
                        
                        analyze_policy(
                            f'{role_name}:{policy_name}', 
                            policy_document, 
                            'inline_role',
                            {'role': role_name, 'policy': policy_name},
                            affected_policies
                        )
                    except Exception as e:
                        logger.warning(f'Error processing inline policy {policy_name} for role {role_name}: {str(e)}')
            except Exception as e:
                logger.warning(f'Error processing role {role_name}: {str(e)}')
    
    # Get inline policies for users
    paginator = iam_client.get_paginator('list_users')
    for page in paginator.paginate():
        for user in page['Users']:
            user_name = user['UserName']
            try:
                # List inline policies for the user
                inline_policies = iam_client.list_user_policies(UserName=user_name)['PolicyNames']
                for policy_name in inline_policies:
                    try:
                        policy_document = iam_client.get_user_policy(
                            UserName=user_name,
                            PolicyName=policy_name
                        )['PolicyDocument']
                        
                        analyze_policy(
                            f'{user_name}:{policy_name}', 
                            policy_document, 
                            'inline_user',
                            {'user': user_name, 'policy': policy_name},
                            affected_policies
                        )
                    except Exception as e:
                        logger.warning(f'Error processing inline policy {policy_name} for user {user_name}: {str(e)}')
            except Exception as e:
                logger.warning(f'Error processing user {user_name}: {str(e)}')
    
    # Get inline policies for groups
    paginator = iam_client.get_paginator('list_groups')
    for page in paginator.paginate():
        for group in page['Groups']:
            group_name = group['GroupName']
            try:
                # List inline policies for the group
                inline_policies = iam_client.list_group_policies(GroupName=group_name)['PolicyNames']
                for policy_name in inline_policies:
                    try:
                        policy_document = iam_client.get_group_policy(
                            GroupName=group_name,
                            PolicyName=policy_name
                        )['PolicyDocument']
                        
                        analyze_policy(
                            f'{group_name}:{policy_name}', 
                            policy_document, 
                            'inline_group',
                            {'group': group_name, 'policy': policy_name},
                            affected_policies
                        )
                    except Exception as e:
                        logger.warning(f'Error processing inline policy {policy_name} for group {group_name}: {str(e)}')
            except Exception as e:
                logger.warning(f'Error processing group {group_name}: {str(e)}')
    
    return affected_policies

def analyze_policy(policy_name, policy_document, policy_type, policy_id, affected_policies):
    needs_updates = False
    old_actions = []
    new_actions = []
    
    # Check if policy uses old aws-portal actions
    try:
        statements = policy_document.get('Statement', [])
        if not isinstance(statements, list):
            statements = [statements]
            
        for statement in statements:
            if statement.get('Effect') == 'Allow':
                actions = statement.get('Action', [])
                if not isinstance(actions, list):
                    actions = [actions]
                
                for action in actions:
                    if action.startswith('aws-portal:'):
                        needs_updates = True
                        old_actions.append(action)
                        if action in ACTION_MAPPING:
                            new_actions.extend(ACTION_MAPPING[action])
                            
                            # Add Billing Conductor specific permissions if enabled
                            if INCLUDE_BILLING_CONDUCTOR and action in BILLING_CONDUCTOR_MAPPING:
                                new_actions.extend(BILLING_CONDUCTOR_MAPPING[action])
                                
                            # Add CUR specific permissions if enabled
                            if INCLUDE_CUR and action in CUR_MAPPING:
                                new_actions.extend(CUR_MAPPING[action])
        
        if needs_updates:
            affected_policies[policy_name] = {
                'policy_type': policy_type,
                'policy_id': policy_id,
                'old_actions': list(set(old_actions)),
                'new_actions': list(set(new_actions)),
                'needs_updates': needs_updates,
                'policy_document': policy_document
            }
    except Exception as e:
        logger.error(f'Error analyzing policy {policy_name}: {str(e)}')

def update_policies(iam_client, affected_policies):
    updated_count = 0
    skipped_count = 0
    
    for policy_name, policy_data in affected_policies.items():
        try:
            if not policy_data['needs_updates']:
                skipped_count += 1
                continue
                
            policy_document = policy_data['policy_document']
            statements = policy_document.get('Statement', [])
            if not isinstance(statements, list):
                statements = [statements]
            
            # Add new actions to the policy
            new_statements = []
            for statement in statements:
                if statement.get('Effect') == 'Allow':
                    actions = statement.get('Action', [])
                    if not isinstance(actions, list):
                        actions = [actions]
                    
                    for action in actions:
                        if action.startswith('aws-portal:') and action in ACTION_MAPPING:
                            # Keep old action and add new ones
                            if action not in actions:
                                actions.append(action)
                            for new_action in ACTION_MAPPING[action]:
                                if new_action not in actions:
                                    actions.append(new_action)
                                    
                            # Add Billing Conductor permissions if enabled
                            if INCLUDE_BILLING_CONDUCTOR and action in BILLING_CONDUCTOR_MAPPING:
                                for new_action in BILLING_CONDUCTOR_MAPPING[action]:
                                    if new_action not in actions:
                                        actions.append(new_action)
                                        
                            # Add CUR permissions if enabled
                            if INCLUDE_CUR and action in CUR_MAPPING:
                                for new_action in CUR_MAPPING[action]:
                                    if new_action not in actions:
                                        actions.append(new_action)
                    
                    statement['Action'] = actions
                new_statements.append(statement)
            
            policy_document['Statement'] = new_statements
            
            # Update the policy based on type
            if policy_data['policy_type'] == 'managed':
                policy_arn = policy_data['policy_id']
                
                # Create new policy version
                response = iam_client.create_policy_version(
                    PolicyArn=policy_arn,
                    PolicyDocument=json.dumps(policy_document),
                    SetAsDefault=True
                )
                logger.info(f'Updated managed policy: {policy_name}')
                
                # Clean up old versions (AWS limits to 5 versions)
                versions = iam_client.list_policy_versions(PolicyArn=policy_arn)['Versions']
                if len(versions) >= 5:
                    # Sort versions by creation date (oldest first)
                    versions.sort(key=lambda x: x['CreateDate'])
                    # Delete oldest non-default version
                    for version in versions:
                        if not version['IsDefaultVersion']:
                            iam_client.delete_policy_version(
                                PolicyArn=policy_arn,
                                VersionId=version['VersionId']
                            )
                            break
            
            elif policy_data['policy_type'] == 'inline_role':
                role_name = policy_data['policy_id']['role']
                inline_policy_name = policy_data['policy_id']['policy']
                
                # Update inline policy
                iam_client.put_role_policy(
                    RoleName=role_name,
                    PolicyName=inline_policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                logger.info(f'Updated inline policy {inline_policy_name} for role {role_name}')
            
            elif policy_data['policy_type'] == 'inline_user':
                user_name = policy_data['policy_id']['user']
                inline_policy_name = policy_data['policy_id']['policy']
                
                # Update inline policy
                iam_client.put_user_policy(
                    UserName=user_name,
                    PolicyName=inline_policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                logger.info(f'Updated inline policy {inline_policy_name} for user {user_name}')
            
            elif policy_data['policy_type'] == 'inline_group':
                group_name = policy_data['policy_id']['group']
                inline_policy_name = policy_data['policy_id']['policy']
                
                # Update inline policy
                iam_client.put_group_policy(
                    GroupName=group_name,
                    PolicyName=inline_policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                logger.info(f'Updated inline policy {inline_policy_name} for group {group_name}')
            
            updated_count += 1
        except Exception as e:
            logger.error(f'Error updating policy {policy_name}: {str(e)}')
            skipped_count += 1
    
    logger.info(f'Updated {updated_count} policies, skipped {skipped_count} policies')
    return {'updated': updated_count, 'skipped': skipped_count}

# Support Ticket Functions
def create_support_ticket(event):
    """Create a generic support ticket"""
    support = boto3.client('support', region_name='us-east-1')  # Support API is only available in us-east-1

    case_params = {
        'subject': event.get('subject'),
        'serviceCode': 'billing',
        'categoryCode': event.get('category', 'general-guidance'),
        'severityCode': event.get('severity', 'low'),
        'communicationBody': event.get('body'),
        'ccEmailAddresses': [],
        'language': 'en',
        'issueType': 'customer-service',
    }

    try:
        response = create_support_case_with_retry(support, case_params)
        logger.info(f'Created support case: {response}')

        return {
            'success': True,
            'caseId': response.get('caseId'),
            'ticketId': event.get('ticketId')
        }
    except Exception as e:
        logger.error(f'Error creating support case: {str(e)}')
        raise

def create_backfill_ticket(event, account_id):
    """Create a specialized backfill support ticket"""
    support = boto3.client('support', region_name='us-east-1')  # Support API is only available in us-east-1

    # Extract parameters
    account_id = event.get('accountId', account_id)
    organization_id = event.get('organizationId', ORGANIZATION_ID)
    cur_bucket_name = event.get('curBucketName', f"{CUR_BUCKET_PREFIX}-{account_id}")
    backfill_months = event.get('backfillMonths', 12)

    # Generate standardized subject line
    subject = f'[AUTOMATED] FinOps: Cost Explorer Backfill Request for {account_id}'

    # Generate standardized body
    body = create_backfill_request_body(account_id, organization_id, cur_bucket_name, backfill_months)

    case_params = {
        'subject': subject,
        'serviceCode': 'billing',
        'categoryCode': 'billing',
        'severityCode': 'normal',
        'communicationBody': body,
        'ccEmailAddresses': [],
        'language': 'en',
        'issueType': 'customer-service',
    }

    try:
        response = create_support_case_with_retry(support, case_params)
        logger.info(f'Created backfill support case: {response}')

        return {
            'success': True,
            'caseId': response.get('caseId'),
            'ticketId': event.get('ticketId', f'BF-{int(time.time())}'),
            'accountId': account_id,
            'subject': subject,
            'createdAt': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f'Error creating backfill support case: {str(e)}')
        raise

def create_backfill_request_body(account_id, organization_id, cur_bucket_name, backfill_months):
    """
    Create the body text for Cost Explorer backfill support tickets
    Provides standardized format with organization context
    """
    # Calculate date ranges for clarity
    today = datetime.now()
    end_date = today
    start_date = today - timedelta(days=30*backfill_months)

    # Format dates as YYYY-MM-DD
    format_date = lambda date: date.strftime('%Y-%m-%d')

    return f"""Hello AWS Support,

This is an automated request for Cost Explorer data backfill for the following member account in our organization:

Account ID: {account_id}
Organization ID: {organization_id}
Backfill Period: {backfill_months} months ({format_date(start_date)} to {format_date(end_date)})

This member account is part of our AWS Organization and we have already set up a centralized Cost and Usage Report (CUR) with the following details:

CUR Bucket: {cur_bucket_name}
Report Path: organization/{organization_id}/{account_id}

We need historical Cost Explorer data for this account to align with our organization-wide cost management and optimization initiatives. Please backfill the Cost Explorer data with the following specifications:

- Granularity: Daily AND Hourly (if possible)
- Include resource-level data
- Include all available services and metrics
- Match data available in our CUR reports

This backfill will allow us to properly analyze historical spend patterns and make informed decisions about cost optimization for this account within our organization.

Thank you for your assistance.

Regards,
AWS Organization Billing Pipeline Team"""

def create_support_case_with_retry(support_client, case_params):
    """
    Create a support case with retry logic
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f'Creating support case: attempt {attempt}')
            return support_client.create_case(**case_params)
        except ClientError as error:
            last_error = error

            # Check if error is retryable
            if error.response['Error']['Code'] in ['ThrottlingException', 'TooManyRequestsException', 'InternalServerError']:
                # Exponential backoff with jitter
                delay = RETRY_DELAY_MS * 2 ** (attempt - 1) * (0.5 + 0.5 * random.random())
                logger.warning(f'Retryable error, will retry after {delay}ms', extra={
                    'attempt': attempt,
                    'errorCode': error.response['Error']['Code'],
                })

                time.sleep(delay / 1000)  # Convert ms to seconds
                continue

            # Non-retryable error
            logger.error(f'Non-retryable error creating support case: {error}')
            raise error

    # If we reach here, all retries failed
    logger.error(f'All {MAX_RETRIES} attempts to create support case failed')
    raise last_error

def get_support_ticket(event):
    """Get a support ticket status"""
    support = boto3.client('support', region_name='us-east-1')

    try:
        response = support.describe_cases(
            caseIdList=[event.get('caseId')],
            includeResolvedCases=True
        )

        if response.get('cases') and len(response['cases']) > 0:
            case = response['cases'][0]
            return {
                'success': True,
                'caseId': event.get('caseId'),
                'ticketId': event.get('ticketId'),
                'status': case.get('status'),
                'subject': case.get('subject'),
                'timeCreated': case.get('timeCreated'),
                'recentCommunications': case.get('recentCommunications', {})
            }
        else:
            return {
                'success': False,
                'message': 'Case not found',
                'caseId': event.get('caseId')
            }
    except Exception as e:
        logger.error(f'Error getting support case: {str(e)}')
        raise

def notify_management_account(event):
    """Notify the management account about ticket events"""
    events_client = boto3.client('events')
    
    try:
        # Configure the event details
        detail = {
            'source': 'billing-policy-migrator',
            'accountId': event.get('accountId'),
            'caseId': event.get('caseId'),
            'ticketId': event.get('ticketId'),
            'message': event.get('message'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Put the event on the default event bus
        response = events_client.put_events(
            Entries=[
                {
                    'Source': 'billing-utilities',
                    'DetailType': event.get('detailType', 'Support Ticket Update'),
                    'Detail': json.dumps(detail),
                    'EventBusName': 'default'
                }
            ]
        )
        
        return {
            'success': True,
            'eventId': response.get('Entries', [{}])[0].get('EventId'),
            'message': 'Notification sent to management account'
        }
    except Exception as e:
        logger.error(f'Error notifying management account: {str(e)}')
        raise 