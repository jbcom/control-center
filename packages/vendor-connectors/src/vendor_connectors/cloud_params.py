"""Cloud API call parameter utilities.

These utilities help build properly formatted parameter dictionaries for
various cloud provider APIs (AWS, Google Cloud, etc.).

The functions handle common patterns like:
- Pagination limits (MaxResults/maxResults)
- Key casing transformations (PascalCase for AWS, camelCase for Google)
- Null/empty value filtering
"""

from __future__ import annotations

from typing import Any

from extended_data_types import is_nothing, lower_first_char, upper_first_char


def get_cloud_call_params(
    max_results: int | None = 10,
    no_max_results: bool = False,
    reject_null: bool = True,
    first_letter_to_lower: bool = False,
    first_letter_to_upper: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a parameter dictionary for cloud API calls.

    This function creates properly formatted parameter dictionaries for
    cloud provider API calls, handling common patterns like pagination
    limits and key casing.

    Args:
        max_results: Maximum number of results to return. Defaults to 10.
        no_max_results: If True, don't include MaxResults in params.
        reject_null: If True, exclude None/empty values from params.
        first_letter_to_lower: Convert param keys to camelCase.
        first_letter_to_upper: Convert param keys to PascalCase.
        **kwargs: Additional parameters to include.

    Returns:
        A dictionary of parameters ready for the cloud API call.

    Examples:
        >>> get_cloud_call_params(max_results=100, NextToken="abc123")
        {'MaxResults': 100, 'NextToken': 'abc123'}

        >>> get_cloud_call_params(first_letter_to_lower=True, pageToken="xyz")
        {'maxResults': 10, 'pageToken': 'xyz'}
    """
    params = {k: v for k, v in kwargs.items() if not is_nothing(v) or not reject_null}

    # Use 'is not None' to handle max_results=0 correctly
    if max_results is not None and not no_max_results:
        params["MaxResults"] = max_results

    if not first_letter_to_lower and not first_letter_to_upper:
        return params

    if first_letter_to_lower:
        params = {lower_first_char(k): v for k, v in params.items()}

    if first_letter_to_upper:
        params = {upper_first_char(k): v for k, v in params.items()}

    return params


def get_aws_call_params(max_results: int | None = 100, **kwargs: Any) -> dict[str, Any]:
    """Build parameters for AWS API calls.

    AWS APIs typically use PascalCase keys (e.g., MaxResults, NextToken).
    Defaults to 100 results per page.

    Args:
        max_results: Maximum number of results. Defaults to 100.
        **kwargs: Additional parameters (will be PascalCased).

    Returns:
        Parameter dictionary with PascalCase keys.

    Examples:
        >>> get_aws_call_params(NextToken="abc")
        {'MaxResults': 100, 'NextToken': 'abc'}

        >>> get_aws_call_params(max_results=50, IdentityStoreId="d-123")
        {'MaxResults': 50, 'IdentityStoreId': 'd-123'}
    """
    return get_cloud_call_params(max_results=max_results, first_letter_to_upper=True, **kwargs)


def get_google_call_params(
    max_results: int | None = 200, no_max_results: bool = False, **kwargs: Any
) -> dict[str, Any]:
    """Build parameters for Google Cloud API calls.

    Google APIs typically use camelCase keys (e.g., maxResults, pageToken).
    Defaults to 200 results per page.

    Args:
        max_results: Maximum number of results. Defaults to 200.
        no_max_results: If True, don't include maxResults in params.
        **kwargs: Additional parameters (will be camelCased).

    Returns:
        Parameter dictionary with camelCase keys.

    Examples:
        >>> get_google_call_params(pageToken="xyz")
        {'maxResults': 200, 'pageToken': 'xyz'}

        >>> get_google_call_params(no_max_results=True, customer_id="C123")
        {'customerId': 'C123'}
    """
    return get_cloud_call_params(
        max_results=max_results,
        no_max_results=no_max_results,
        first_letter_to_lower=True,
        **kwargs,
    )


__all__ = [
    "get_cloud_call_params",
    "get_aws_call_params",
    "get_google_call_params",
]
