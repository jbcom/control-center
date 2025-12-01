"""
Secrets Merging Lambda Handler - thin shim to terraform_modules library.

This module provides the Lambda entry point that delegates to the terraform_modules
library's lambda_handler. The actual merging logic lives in terraform_modules.__main__.

The TM_OPERATION environment variable is set to "merge_secrets" in the SAM template,
so the handler automatically routes to the merge_secrets operation.
"""

from terraform_modules.__main__ import lambda_handler

# Re-export for Lambda runtime to discover
__all__ = ["lambda_handler"]
