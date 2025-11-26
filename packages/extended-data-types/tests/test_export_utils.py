"""This module contains test functions for verifying the functionality of wrapping raw YAML data for export using the
`extended_data_types` package. It includes fixtures for simple and complex YAML data and tests for ensuring the proper
encoding and wrapping of this data.

Fixtures:
    - simple_yaml_fixture: Provides a simple YAML string for testing.
    - complex_yaml_fixture: Provides a complex YAML string representing an AWS CloudFormation template for testing.

Functions:
    - test_wrap_raw_data_for_export_yaml: Tests wrapping and encoding of simple YAML data.
    - test_wrap_raw_data_for_export_yaml_complex: Tests wrapping and encoding of complex YAML data.
"""

from __future__ import annotations

import datetime
import json
import pathlib

import pytest

from extended_data_types.export_utils import (
    make_raw_data_export_safe,
    wrap_raw_data_for_export,
)
from extended_data_types.yaml_utils import decode_yaml


@pytest.fixture
def simple_yaml_fixture() -> str:
    """Provides a simple YAML string for testing.

    Returns:
        str: A simple YAML string.
    """
    return "test_key: test_value\nnested:\n  key1: value1\n  key2: value2\nlist:\n  - item1\n  - item2\n"


@pytest.fixture
def complex_yaml_fixture() -> str:
    """Provides a complex YAML string representing an AWS CloudFormation template for testing.

    Returns:
        str: A complex YAML string.
    """
    return """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyBucket:
    Type: 'AWS::S3::Bucket'
    Properties:
      BucketName: !Sub '${AWS::StackName}-bucket'
      Tags:
        - Key: Name
          Value: !Ref 'AWS::StackName'
Outputs:
  BucketName:
    Value: !Ref MyBucket
    Description: Name of the bucket
"""


def test_wrap_raw_data_for_export_yaml(simple_yaml_fixture: str) -> None:
    """Tests wrapping and encoding of simple YAML data.

    Args:
        simple_yaml_fixture (str): A simple YAML string provided by the fixture.

    Asserts:
        The result of wrap_raw_data_for_export contains key parts of the original YAML string.
    """
    result = wrap_raw_data_for_export(
        decode_yaml(simple_yaml_fixture),
        allow_encoding="yaml",
    )
    assert "test_key: test_value" in result
    assert "key1: value1" in result


def test_wrap_raw_data_for_export_yaml_complex(complex_yaml_fixture: str) -> None:
    """Tests wrapping and encoding of complex YAML data.

    Args:
        complex_yaml_fixture (str): A complex YAML string provided by the fixture.

    Asserts:
        The result of wrap_raw_data_for_export contains key parts of the original YAML string.
    """
    result = wrap_raw_data_for_export(
        decode_yaml(complex_yaml_fixture),
        allow_encoding="yaml",
    )
    assert 'AWSTemplateFormatVersion: "2010-09-09"' in result
    assert 'Type: "AWS::S3::Bucket"' in result


def test_make_raw_data_export_safe_tuple_with_datetime() -> None:
    """Tests that tuples containing datetime objects are properly converted.

    Asserts:
        - Tuples are converted to lists
        - datetime objects within tuples are converted to ISO format strings
        - The result can be serialized to JSON
    """
    test_date = datetime.date(2025, 1, 15)
    test_datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)

    data = {
        "tuple_with_dates": (test_date, test_datetime, "string"),
        "nested": {"tuple_dates": (test_date, test_datetime)},
    }

    result = make_raw_data_export_safe(data)

    # Check that tuples were converted to lists
    assert isinstance(result["tuple_with_dates"], list)
    assert isinstance(result["nested"]["tuple_dates"], list)

    # Check that datetime objects were converted to strings
    assert result["tuple_with_dates"][0] == "2025-01-15"
    assert result["tuple_with_dates"][1] == "2025-01-15T12:30:45"
    assert result["tuple_with_dates"][2] == "string"

    assert result["nested"]["tuple_dates"][0] == "2025-01-15"
    assert result["nested"]["tuple_dates"][1] == "2025-01-15T12:30:45"

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_tuple_with_path() -> None:
    """Tests that tuples containing Path objects are properly converted.

    Asserts:
        - Tuples are converted to lists
        - Path objects within tuples are converted to strings
        - The result can be serialized to JSON
    """
    path1 = pathlib.Path("/tmp/file1.txt")
    path2 = pathlib.Path("/home/user/file2.txt")

    data = {
        "tuple_with_paths": (path1, path2, "regular_string"),
        "list_of_tuples": [(path1, "item1"), (path2, "item2")],
    }

    result = make_raw_data_export_safe(data)

    # Check that tuples were converted to lists
    assert isinstance(result["tuple_with_paths"], list)
    assert isinstance(result["list_of_tuples"][0], list)
    assert isinstance(result["list_of_tuples"][1], list)

    # Check that Path objects were converted to strings
    assert result["tuple_with_paths"][0] == "/tmp/file1.txt"
    assert result["tuple_with_paths"][1] == "/home/user/file2.txt"
    assert result["tuple_with_paths"][2] == "regular_string"

    assert result["list_of_tuples"][0][0] == "/tmp/file1.txt"
    assert result["list_of_tuples"][0][1] == "item1"
    assert result["list_of_tuples"][1][0] == "/home/user/file2.txt"
    assert result["list_of_tuples"][1][1] == "item2"

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_tuple_mixed_types() -> None:
    """Tests that tuples with mixed complex types are properly converted.

    Asserts:
        - Tuples with datetime, Path, and regular types are all converted properly
        - Nested tuples are handled correctly
    """
    test_date = datetime.date(2025, 1, 15)
    test_path = pathlib.Path("/tmp/test.txt")

    data = {
        "mixed_tuple": (test_date, test_path, 42, "string", 3.14),
        "nested_tuples": ((test_date, test_path), (1, 2, 3)),
    }

    result = make_raw_data_export_safe(data)

    # Check outer tuple conversion
    assert isinstance(result["mixed_tuple"], list)
    assert result["mixed_tuple"][0] == "2025-01-15"
    assert result["mixed_tuple"][1] == "/tmp/test.txt"
    assert result["mixed_tuple"][2] == 42
    assert result["mixed_tuple"][3] == "string"
    assert result["mixed_tuple"][4] == 3.14

    # Check nested tuple conversion
    assert isinstance(result["nested_tuples"], list)
    assert isinstance(result["nested_tuples"][0], list)
    assert isinstance(result["nested_tuples"][1], list)
    assert result["nested_tuples"][0][0] == "2025-01-15"
    assert result["nested_tuples"][0][1] == "/tmp/test.txt"
    assert result["nested_tuples"][1] == [1, 2, 3]

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_empty_tuple() -> None:
    """Tests that empty tuples are properly converted to empty lists.

    Asserts:
        - Empty tuples are converted to empty lists
    """
    data = {"empty_tuple": (), "list_with_empty_tuple": [(), 1, 2]}

    result = make_raw_data_export_safe(data)

    assert isinstance(result["empty_tuple"], list)
    assert len(result["empty_tuple"]) == 0
    assert isinstance(result["list_with_empty_tuple"][0], list)
    assert len(result["list_with_empty_tuple"][0]) == 0


def test_make_raw_data_export_safe_frozenset_with_datetime() -> None:
    """Tests that frozensets containing datetime objects are properly converted.

    Asserts:
        - Frozensets are converted to lists
        - datetime objects within frozensets are converted to ISO format strings
        - The result can be serialized to JSON
    """
    test_date = datetime.date(2025, 1, 15)
    test_datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)

    data = {
        "frozenset_with_dates": frozenset([test_date, test_datetime]),
        "nested": {"frozenset_dates": frozenset([test_date])},
    }

    result = make_raw_data_export_safe(data)

    # Check that frozensets were converted to lists
    assert isinstance(result["frozenset_with_dates"], list)
    assert isinstance(result["nested"]["frozenset_dates"], list)

    # Check that datetime objects were converted to strings
    assert "2025-01-15" in result["frozenset_with_dates"]
    assert "2025-01-15T12:30:45" in result["frozenset_with_dates"]
    assert result["nested"]["frozenset_dates"][0] == "2025-01-15"

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_frozenset_with_path() -> None:
    """Tests that frozensets containing Path objects are properly converted.

    Asserts:
        - Frozensets are converted to lists
        - Path objects within frozensets are converted to strings
        - The result can be serialized to JSON
    """
    path1 = pathlib.Path("/tmp/file1.txt")
    path2 = pathlib.Path("/home/user/file2.txt")

    data = {
        "frozenset_with_paths": frozenset([path1, path2]),
    }

    result = make_raw_data_export_safe(data)

    # Check that frozenset was converted to list
    assert isinstance(result["frozenset_with_paths"], list)

    # Check that Path objects were converted to strings
    assert "/tmp/file1.txt" in result["frozenset_with_paths"]
    assert "/home/user/file2.txt" in result["frozenset_with_paths"]

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None
