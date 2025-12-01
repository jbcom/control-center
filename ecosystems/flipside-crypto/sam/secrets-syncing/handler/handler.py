"""
Secrets Syncing Lambda Handler - thin shim to terraform_modules library.

This module provides the Lambda entry point that delegates to the terraform_modules
library's lambda_handler. The actual syncing logic lives in terraform_modules.__main__.

The TM_OPERATION environment variable is set to "sync_secrets" in the SAM template,
so the handler automatically routes to the sync_secrets operation.

This function is triggered by S3 ObjectCreated events when the merging lambda
writes new merged secrets files (secrets/{target}.json).
"""

from terraform_modules.__main__ import lambda_handler

# Re-export for Lambda runtime to discover
__all__ = ["lambda_handler"]
