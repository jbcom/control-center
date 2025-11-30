"""Tests for decorator-based DirectedInputsClass integrations."""

from __future__ import annotations

import pytest

from directed_inputs_class import directed_inputs, input_config


@directed_inputs(inputs={"domain": "example.com"})
class ExampleService:
    """Simple service used for decorator tests."""

    def list_users(self, domain: str) -> str:
        return domain

    @input_config("api_key", source_name="API_KEY", required=True)
    def secure_call(self, api_key: str) -> str:
        return api_key

    @input_config("config", decode_from_json=True)
    def parse_config(self, config: dict[str, str]) -> dict[str, str]:
        return config

    def greet(self, prefix: str = "hello") -> str:
        return prefix


def test_decorator_populates_missing_argument() -> None:
    service = ExampleService()
    assert service.list_users() == "example.com"


def test_provided_argument_is_not_overwritten() -> None:
    service = ExampleService()
    assert service.list_users(domain="override") == "override"


def test_required_input_uses_custom_source() -> None:
    service = ExampleService(
        _directed_inputs_config={"inputs": {"API_KEY": "super-secret"}}
    )
    assert service.secure_call() == "super-secret"


def test_missing_required_input_raises_error() -> None:
    service = ExampleService(_directed_inputs_config={"inputs": {"domain": "acme.io"}})
    with pytest.raises(RuntimeError):
        service.secure_call()


def test_decode_from_json_input_config() -> None:
    service = ExampleService(
        _directed_inputs_config={"inputs": {"config": '{"enabled": true}'}}
    )
    assert service.parse_config() == {"enabled": True}


def test_method_default_used_when_input_missing() -> None:
    service = ExampleService(_directed_inputs_config={"inputs": {"domain": "acme.io"}})
    assert service.greet() == "hello"


def test_refresh_inputs_updates_context() -> None:
    service = ExampleService(
        _directed_inputs_config={"inputs": {"domain": "override.io"}}
    )
    assert service.list_users() == "override.io"
    service.refresh_inputs(inputs={"domain": "beta.example"})
    assert service.list_users() == "beta.example"
