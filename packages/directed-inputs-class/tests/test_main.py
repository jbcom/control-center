"""Test suite for the DirectedInputsClass.

This module contains unit tests for the DirectedInputsClass, which manages
and processes directed inputs from various sources like environment variables,
stdin, and predefined dictionaries.

The tests cover initialization, input retrieval, decoding, and input management
functions such as freezing, thawing, and shifting inputs.

Fixtures:
    _env_setup: A pytest fixture to set up environment variables for tests.
    _stdin_setup: A pytest fixture to set up stdin for tests.

Tests:
    test_init_with_env_vars: Tests initialization with environment variables.
    test_init_with_stdin: Tests initialization with stdin input.
    test_get_input_with_default: Tests retrieving an input with a default value.
    test_get_input_required: Tests retrieving a required input.
    test_get_input_boolean: Tests retrieving and converting a boolean input.
    test_get_input_integer: Tests retrieving and converting an integer input.
    test_decode_input_json: Tests decoding an input from JSON format.
    test_decode_input_yaml: Tests decoding an input from YAML format.
    test_decode_input_base64: Tests decoding an input from Base64 format.
    test_freeze_inputs: Tests freezing inputs.
    test_thaw_inputs: Tests thawing inputs.
    test_shift_inputs: Tests shifting between frozen and thawed inputs.
"""

from __future__ import annotations

import json
import os

from pathlib import Path

import pytest

from directed_inputs_class.__main__ import DirectedInputsClass
from extended_data_types import base64_encode


@pytest.fixture
def _env_setup(monkeypatch):
    """Fixture to set up environment variables.

    This fixture sets an environment variable `TEST_ENV_VAR` with the value
    `test_value` to simulate environment variable inputs during tests.

    Args:
        monkeypatch: A pytest fixture for safely patching and modifying the environment.
    """
    monkeypatch.setenv("TEST_ENV_VAR", "test_value")


@pytest.fixture
def _stdin_setup(monkeypatch):
    """Fixture to set up stdin.

    This fixture redirects stdin to a dummy file to simulate stdin inputs
    during tests.

    Args:
        monkeypatch: A pytest fixture for safely patching and modifying stdin.
    """
    with Path(os.devnull).open("w") as f:
        monkeypatch.setattr("sys.stdin", f)


@pytest.mark.usefixtures("_env_setup")
def test_init_with_env_vars():
    """Test initialization with environment variables.

    This test verifies that the DirectedInputsClass correctly initializes with
    inputs from environment variables.
    """
    dic = DirectedInputsClass()
    assert dic.inputs["TEST_ENV_VAR"] == "test_value"


@pytest.mark.usefixtures("_env_setup")
def test_init_with_stdin(monkeypatch):
    """Test initialization with stdin input.

    This test verifies that the DirectedInputsClass correctly initializes with
    inputs from stdin when `from_stdin` is set to True.

    Args:
        monkeypatch: A pytest fixture for safely patching stdin.
    """
    input_data = json.dumps({"stdin_key": "stdin_value"})
    monkeypatch.setattr("sys.stdin.read", lambda: input_data)

    dic = DirectedInputsClass(from_stdin=True)
    assert dic.inputs["stdin_key"] == "stdin_value"


def test_get_input_with_default():
    """Test retrieving an input with a default value.

    This test verifies that the DirectedInputsClass retrieves an input correctly,
    returning a default value if the key is not found.
    """
    dic = DirectedInputsClass(inputs={"key1": "value1"})
    assert dic.get_input("key1", default="default_value") == "value1"
    assert dic.get_input("key2", default="default_value") == "default_value"


def test_get_input_required():
    """Test retrieving a required input.

    This test verifies that the DirectedInputsClass raises an error if a required
    input is not provided.
    """
    dic = DirectedInputsClass(inputs={"key1": "value1"})
    with pytest.raises(RuntimeError, match="Required input key2 not passed"):
        dic.get_input("key2", required=True)


def test_get_input_boolean():
    """Test retrieving and converting a boolean input.

    This test verifies that the DirectedInputsClass correctly retrieves an input
    and converts it to a boolean value.
    """
    dic = DirectedInputsClass(inputs={"bool_key": "true"})
    assert dic.get_input("bool_key", is_bool=True) is True


def test_get_input_boolean_existing_bool():
    """Boolean inputs that are already bool are returned unchanged."""
    dic = DirectedInputsClass(inputs={"bool_key": False})
    assert dic.get_input("bool_key", is_bool=True) is False


def test_get_input_integer():
    """Test retrieving and converting an integer input.

    This test verifies that the DirectedInputsClass correctly retrieves an input
    and converts it to an integer value.
    """
    dic = DirectedInputsClass(inputs={"int_key": "10"})
    integer_test_value = 10
    assert dic.get_input("int_key", is_integer=True) == integer_test_value


def test_decode_input_json():
    """Test decoding an input from JSON format.

    This test verifies that the DirectedInputsClass correctly decodes an input
    from JSON format.
    """
    dic = DirectedInputsClass(inputs={"json_key": '{"name": "test"}'})
    decoded = dic.decode_input("json_key", decode_from_json=True)
    assert decoded == {"name": "test"}


def test_decode_input_yaml():
    """Test decoding an input from YAML format.

    This test verifies that the DirectedInputsClass correctly decodes an input
    from YAML format.
    """
    dic = DirectedInputsClass(inputs={"yaml_key": "name: test"})
    decoded = dic.decode_input("yaml_key", decode_from_yaml=True)
    assert decoded == {"name": "test"}


def test_decode_input_base64():
    """Test decoding an input from Base64 format.

    This test verifies that the DirectedInputsClass correctly decodes an input
    from Base64 format, optionally also decoding it from JSON.
    """
    encoded_value = base64_encode(json.dumps({"name": "test"}).encode())
    dic = DirectedInputsClass(inputs={"base64_key": encoded_value})
    decoded = dic.decode_input(
        "base64_key", decode_from_base64=True, decode_from_json=True
    )
    assert decoded == {"name": "test"}


def test_decode_input_base64_from_bytes():
    """Base64 encoded bytes can be decoded and parsed."""
    encoded_value = base64_encode(json.dumps({"name": "test"}).encode())
    dic = DirectedInputsClass(inputs={"base64_key": encoded_value.encode()})
    decoded = dic.decode_input(
        "base64_key", decode_from_base64=True, decode_from_json=True
    )

    assert decoded == {"name": "test"}


def test_freeze_inputs():
    """Test freezing inputs.

    This test verifies that the DirectedInputsClass correctly freezes its inputs,
    preventing further modifications.
    """
    dic = DirectedInputsClass(inputs={"key1": "value1"})
    frozen_inputs = dic.freeze_inputs()
    assert frozen_inputs["key1"] == "value1"
    assert dic.inputs == {}


def test_thaw_inputs():
    """Test thawing inputs.

    This test verifies that the DirectedInputsClass correctly thaws its inputs,
    merging the frozen inputs back into the current inputs.
    """
    dic = DirectedInputsClass(inputs={"key1": "value1"})
    dic.freeze_inputs()
    dic.thaw_inputs()
    assert dic.inputs["key1"] == "value1"
    assert dic.frozen_inputs == {}


def test_shift_inputs():
    """Test shifting between frozen and thawed inputs.

    This test verifies that the DirectedInputsClass correctly shifts between
    frozen and thawed inputs, allowing for flexible input management.
    """
    dic = DirectedInputsClass(inputs={"key1": "value1"})
    dic.shift_inputs()
    assert dic.inputs == {}
    assert dic.frozen_inputs["key1"] == "value1"

    dic.shift_inputs()
    assert dic.inputs["key1"] == "value1"
    assert dic.frozen_inputs == {}


def test_merge_inputs_deep_merge():
    """Merging inputs should deep merge nested structures rather than replace."""
    dic = DirectedInputsClass(inputs={"nested": {"left": 1}})
    merged = dic.merge_inputs({"nested": {"right": 2}})

    assert merged["nested"] == {"left": 1, "right": 2}


def test_environment_prefix_filter(monkeypatch):
    """Only environment variables matching the prefix should be loaded."""
    monkeypatch.setenv("APP_ALPHA", "alpha")
    monkeypatch.setenv("APP_BETA", "beta")
    monkeypatch.setenv("UNSCOPED", "nope")

    dic = DirectedInputsClass(
        from_environment=True, env_prefix="APP_", strip_env_prefix=True
    )

    assert dic.inputs["ALPHA"] == "alpha"
    assert dic.inputs["BETA"] == "beta"
    assert "UNSCOPED" not in dic.inputs
