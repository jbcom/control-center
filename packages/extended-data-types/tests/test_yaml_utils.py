"""This module contains test functions for verifying the functionality of YAML encoding and decoding using the
`extended_data_types` package. It includes fixtures for simple and complex YAML data, and tests for encoding,
decoding, and handling custom YAML tags and pairs.

Fixtures:
    - simple_yaml_fixture: Provides a simple YAML string for testing.
    - complex_yaml_fixture: Provides a complex YAML string representing an AWS CloudFormation template for testing.

Functions:
    - test_encode_yaml: Tests encoding of YAML data to string format.
    - test_yaml_construct_undefined: Tests decoding of YAML data with a custom tag.
    - test_yaml_represent_tagged: Tests encoding of YAMLTagged data to string format.
    - test_yaml_pairs_representation: Tests encoding of YamlPairs data to string format.
    - test_decode_and_encode_complex_yaml: Tests decoding and encoding of complex YAML data.
"""

from __future__ import annotations

import pytest

from extended_data_types.yaml_utils import (
    YamlPairs,
    YamlTagged,
    decode_yaml,
    encode_yaml,
)


CUSTOM_TAG_VALUE = 12345


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


def test_encode_yaml(simple_yaml_fixture: str) -> None:
    """Tests encoding of YAML data to string format.

    Args:
        simple_yaml_fixture (str): A simple YAML string provided by the fixture.

    Asserts:
        The encoded and then decoded data matches the original data.
    """
    data = decode_yaml(simple_yaml_fixture)
    result = encode_yaml(data)
    expected_data = decode_yaml(simple_yaml_fixture)
    result_data = decode_yaml(result)
    assert result_data == expected_data


def test_yaml_construct_undefined() -> None:
    """Tests decoding of YAML data with a custom tag.

    Asserts:
        The decoded data is an instance of YamlTagged with the expected tag and values.
    """
    custom_tag_yaml_fixture = "!CustomTag\nname: custom\nvalue: 12345\n"
    data = decode_yaml(custom_tag_yaml_fixture)
    assert isinstance(data, YamlTagged)
    assert data.tag == "!CustomTag"
    assert data["name"] == "custom"
    assert data["value"] == CUSTOM_TAG_VALUE


def test_yaml_represent_tagged() -> None:
    """Tests encoding of YamlTagged data to string format.

    Asserts:
        The encoded string contains the custom tag and the expected key-value pairs.
    """
    data = YamlTagged("!CustomTag", {"name": "custom", "value": CUSTOM_TAG_VALUE})
    encoded_data = encode_yaml(data)
    assert "!CustomTag" in encoded_data
    assert "name: custom" in encoded_data
    assert f"value: {CUSTOM_TAG_VALUE}" in encoded_data


def test_yaml_pairs_representation() -> None:
    """Tests encoding of YamlPairs data to string format.

    Asserts:
        The encoded string contains the expected key-value pairs.
    """
    data = YamlPairs([("key1", "value1"), ("key2", "value2")])
    encoded_data = encode_yaml(data)
    assert "key1: value1" in encoded_data
    assert "key2: value2" in encoded_data


def test_decode_and_encode_complex_yaml(complex_yaml_fixture: str) -> None:
    """Tests decoding and encoding of complex YAML data.

    Args:
        complex_yaml_fixture (str): A complex YAML string provided by the fixture.

    Asserts:
        The encoded string contains key elements of the original YAML string.
    """
    data = decode_yaml(complex_yaml_fixture)
    assert isinstance(data, dict), f"Expected dict, but got {type(data)}"
    encoded_data = encode_yaml(data)
    assert "AWSTemplateFormatVersion" in encoded_data
    assert "Resources" in encoded_data
    assert "Outputs" in encoded_data
