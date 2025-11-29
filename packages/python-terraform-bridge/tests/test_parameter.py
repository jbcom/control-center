"""Tests for TerraformModuleParameter."""

from __future__ import annotations

import inspect

from python_terraform_bridge.parameter import TerraformModuleParameter


class TestTerraformModuleParameter:
    """Tests for TerraformModuleParameter class."""

    def test_basic_string_parameter(self) -> None:
        """Test basic string parameter creation."""
        param = TerraformModuleParameter(name="domain")
        assert param.name == "domain"
        assert param.type == "any"  # No default, no *_id suffix -> any
        assert param.required is True

    def test_string_type_inference(self) -> None:
        """Test type inference from string default."""
        param = TerraformModuleParameter(name="value", default="test")
        assert param.type == "string"

    def test_bool_type_inference(self) -> None:
        """Test type inference from bool default."""
        param = TerraformModuleParameter(name="enabled", default=False)
        assert param.type == "bool"

    def test_number_type_inference(self) -> None:
        """Test type inference from int default."""
        param = TerraformModuleParameter(name="count", default=10)
        assert param.type == "number"

    def test_id_suffix_infers_string(self) -> None:
        """Test that *_id suffix infers string type."""
        param = TerraformModuleParameter(name="user_id")
        assert param.type == "string"

    def test_get_variable_required(self) -> None:
        """Test get_variable for required parameter."""
        param = TerraformModuleParameter(
            name="domain",
            required=True,
            type="string",  # Explicit type to test variable generation
            description="Target domain",
        )
        var = param.get_variable()

        assert var["type"] == "string"
        assert "default" not in var
        assert var["description"] == "Target domain"

    def test_get_variable_optional(self) -> None:
        """Test get_variable for optional parameter."""
        param = TerraformModuleParameter(
            name="limit",
            required=False,
            default=100,
            type="number",
        )
        var = param.get_variable()

        assert var["type"] == "number"
        assert var["default"] == 100

    def test_get_variable_sensitive(self) -> None:
        """Test get_variable for sensitive parameter."""
        param = TerraformModuleParameter(
            name="api_key",
            sensitive=True,
        )
        var = param.get_variable()

        assert var["sensitive"] is True

    def test_get_trigger_basic(self) -> None:
        """Test basic trigger generation."""
        param = TerraformModuleParameter(name="domain")
        trigger = param.get_trigger()

        assert trigger == "${try(nonsensitive(var.domain), var.domain)}"

    def test_get_trigger_json_encode(self) -> None:
        """Test trigger with JSON encoding."""
        param = TerraformModuleParameter(name="config", json_encode=True)
        trigger = param.get_trigger()

        assert "jsonencode" in trigger
        assert trigger == "${try(nonsensitive(jsonencode(var.config)), jsonencode(var.config))}"

    def test_get_trigger_base64_encode(self) -> None:
        """Test trigger with base64 encoding."""
        param = TerraformModuleParameter(name="data", base64_encode=True)
        trigger = param.get_trigger()

        assert "base64encode" in trigger

    def test_get_trigger_both_encodings(self) -> None:
        """Test trigger with both encodings."""
        param = TerraformModuleParameter(name="data", json_encode=True, base64_encode=True)
        trigger = param.get_trigger()

        # Both should be applied
        assert "jsonencode" in trigger
        assert "base64encode" in trigger

    def test_get_trigger_disable_encoding(self) -> None:
        """Test trigger with encoding disabled."""
        param = TerraformModuleParameter(name="data", json_encode=True)
        trigger = param.get_trigger(disable_encoding=True)

        assert "jsonencode" not in trigger

    def test_get_trigger_custom(self) -> None:
        """Test custom trigger override."""
        param = TerraformModuleParameter(name="data", trigger="${each.key}")
        trigger = param.get_trigger()

        assert trigger == "${each.key}"

    def test_from_type_hint_string(self) -> None:
        """Test parameter from string type hint."""
        param = TerraformModuleParameter.from_type_hint(
            name="domain",
            type_hint=str,
            default=inspect.Parameter.empty,
        )

        assert param.name == "domain"
        assert param.type == "string"
        assert param.required is True

    def test_from_type_hint_optional(self) -> None:
        """Test parameter from optional with default."""
        param = TerraformModuleParameter.from_type_hint(
            name="limit",
            type_hint=int,
            default=100,
        )

        assert param.required is False
        assert param.default == 100
        assert param.type == "number"

    def test_from_type_hint_dict(self) -> None:
        """Test parameter from dict type hint."""
        param = TerraformModuleParameter.from_type_hint(
            name="config",
            type_hint=dict,
            default=inspect.Parameter.empty,
        )

        assert param.type == "map(any)"
        assert param.json_encode is True
        assert param.base64_encode is True

    def test_from_type_hint_list(self) -> None:
        """Test parameter from list type hint."""
        param = TerraformModuleParameter.from_type_hint(
            name="items",
            type_hint=list,
            default=[],
        )

        assert param.type == "list(any)"
        assert param.required is False
