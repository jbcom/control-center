"""This module contains test functions for verifying the functionality of HCL2 encoding and decoding using the
`extended_data_types` package. It includes fixtures for HCL2 data and expected output, and tests for decoding and
encoding HCL2 data.

Fixtures:
    - hcl2_data: Provides a sample HCL2 string for testing.
    - expected_output: Provides the expected decoded output for the sample HCL2 string.

Functions:
    - test_decode_hcl2_valid: Tests decoding of valid HCL2 data.
    - test_decode_hcl2_empty: Tests decoding of empty HCL2 data.
    - test_decode_hcl2_invalid: Tests decoding of invalid HCL2 data.
    - test_encode_hcl2: Tests encoding of data to HCL2 format.
"""

from __future__ import annotations

import pytest

from extended_data_types.hcl2_utils import decode_hcl2, encode_hcl2
from lark.exceptions import UnexpectedToken


@pytest.fixture
def hcl2_data() -> str:
    """Provides a sample HCL2 string for testing.

    Returns:
        str: A sample HCL2 string.
    """
    return """
    resource "aws_s3_bucket" "b" {
      bucket = "my-tf-test-bucket"
      acl    = "private"

      tags = {
        Name        = "My bucket"
        Environment = "Dev"
      }
    }
    """


@pytest.fixture
def expected_output() -> dict:
    """Provides the expected decoded output for the sample HCL2 string.

    Returns:
        dict: The expected decoded output.
    """
    return {
        "resource": [
            {
                "aws_s3_bucket": {
                    "b": {
                        "bucket": "my-tf-test-bucket",
                        "acl": "private",
                        "tags": {"Name": "My bucket", "Environment": "Dev"},
                    },
                },
            },
        ],
    }


def test_decode_hcl2_valid(hcl2_data: str, expected_output: dict) -> None:
    """Tests decoding of valid HCL2 data.

    Args:
        hcl2_data (str): A sample HCL2 string provided by the fixture.
        expected_output (dict): The expected decoded output provided by the fixture.

    Asserts:
        The result of decode_hcl2 matches the expected output.
    """
    result = decode_hcl2(hcl2_data)
    assert result == expected_output


def test_decode_hcl2_empty() -> None:
    """Tests decoding of empty HCL2 data.

    Asserts:
        The result of decode_hcl2 matches an empty dictionary.
    """
    hcl2_data = ""
    expected_output = {}
    result = decode_hcl2(hcl2_data)
    assert result == expected_output


def test_decode_hcl2_invalid() -> None:
    """Tests decoding of invalid HCL2 data.

    Asserts:
        A UnexpectedToken error is raised with an appropriate error message.
    """
    hcl2_data = "invalid hcl2 data"
    with pytest.raises(UnexpectedToken):
        decode_hcl2(hcl2_data)


def test_encode_hcl2() -> None:
    """Tests encoding of data to HCL2 format.

    Asserts:
        The result of encode_hcl2 matches the expected HCL2 string.
    """
    data = {
        "resource": [
            {
                "aws_s3_bucket": {
                    "b": {
                        "bucket": "my-tf-test-bucket",
                        "acl": "private",
                        "tags": {"Name": "My bucket", "Environment": "Dev"},
                    },
                },
            },
        ],
    }
    expected_hcl2 = """{
  "resource" = [
    {
      "aws_s3_bucket" = {
        "b" = {
          "bucket" = "my-tf-test-bucket",
          "acl" = "private",
          "tags" = {
            "Name" = "My bucket",
            "Environment" = "Dev"
          }
        }
      }
    }
  ]
}"""
    result = encode_hcl2(data)
    assert result == expected_hcl2
