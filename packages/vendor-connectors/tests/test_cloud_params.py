"""Tests for cloud_params module."""

from vendor_connectors.cloud_params import (
    get_aws_call_params,
    get_cloud_call_params,
    get_google_call_params,
)


class TestGetCloudCallParams:
    """Tests for get_cloud_call_params function."""

    def test_default_max_results(self):
        """Default max_results is 10."""
        params = get_cloud_call_params()
        assert params == {"MaxResults": 10}

    def test_custom_max_results(self):
        """Custom max_results is applied."""
        params = get_cloud_call_params(max_results=50)
        assert params == {"MaxResults": 50}

    def test_no_max_results(self):
        """no_max_results excludes MaxResults."""
        params = get_cloud_call_params(no_max_results=True)
        assert "MaxResults" not in params

    def test_max_results_zero(self):
        """max_results=0 should be included (edge case)."""
        params = get_cloud_call_params(max_results=0)
        assert params == {"MaxResults": 0}

    def test_kwargs_included(self):
        """Additional kwargs are included."""
        params = get_cloud_call_params(NextToken="abc123")
        assert params == {"MaxResults": 10, "NextToken": "abc123"}

    def test_reject_null_values(self):
        """None values are rejected by default."""
        params = get_cloud_call_params(NextToken=None, ValidValue="test")
        assert params == {"MaxResults": 10, "ValidValue": "test"}

    def test_include_null_values(self):
        """Null values can be included."""
        params = get_cloud_call_params(reject_null=False, NullValue=None)
        assert "NullValue" in params

    def test_first_letter_to_lower(self):
        """Keys are converted to camelCase."""
        params = get_cloud_call_params(first_letter_to_lower=True, NextToken="abc")
        assert params == {"maxResults": 10, "nextToken": "abc"}

    def test_first_letter_to_upper(self):
        """Keys are converted to PascalCase."""
        params = get_cloud_call_params(first_letter_to_upper=True, nextToken="abc")
        assert params == {"MaxResults": 10, "NextToken": "abc"}


class TestGetAwsCallParams:
    """Tests for get_aws_call_params function."""

    def test_default_max_results(self):
        """AWS default max_results is 100."""
        params = get_aws_call_params()
        assert params == {"MaxResults": 100}

    def test_first_letter_upper(self):
        """AWS params have first letter uppercased."""
        params = get_aws_call_params(NextToken="abc", IdentityStoreId="d-123")
        assert params == {
            "MaxResults": 100,
            "IdentityStoreId": "d-123",
            "NextToken": "abc",
        }

    def test_snake_case_preserved(self):
        """Snake case keys have first letter uppercased only."""
        params = get_aws_call_params(identity_store_id="d-123")
        # Only the first letter is uppercased
        assert params == {
            "MaxResults": 100,
            "Identity_store_id": "d-123",
        }


class TestGetGoogleCallParams:
    """Tests for get_google_call_params function."""

    def test_default_max_results(self):
        """Google default max_results is 200."""
        params = get_google_call_params()
        assert params == {"maxResults": 200}

    def test_first_letter_lower(self):
        """Google params have first letter lowercased."""
        params = get_google_call_params(PageToken="xyz", CustomerId="C123")
        assert params == {
            "maxResults": 200,
            "pageToken": "xyz",
            "customerId": "C123",
        }

    def test_no_max_results(self):
        """no_max_results works for Google."""
        params = get_google_call_params(no_max_results=True, customerId="C123")
        assert "maxResults" not in params
        assert params == {"customerId": "C123"}

    def test_snake_case_preserved(self):
        """Snake case keys have first letter lowercased only."""
        params = get_google_call_params(no_max_results=True, Customer_Id="C123")
        # Only the first letter is lowercased
        assert params == {"customer_Id": "C123"}
