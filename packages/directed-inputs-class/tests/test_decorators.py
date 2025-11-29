"""Tests for decorator-based input handling."""

from __future__ import annotations

import os

from unittest.mock import patch

import pytest

from directed_inputs_class import InputContext, directed_inputs, input_config
from directed_inputs_class import decorators as decorators_mod


class TestDirectedInputsDecorator:
    """Tests for @directed_inputs class decorator."""

    def test_basic_class_decoration(self) -> None:
        """Test that decorator can be applied to a class."""

        @directed_inputs
        class MyService:
            def hello(self) -> str:
                return "world"

        svc = MyService()
        assert svc.hello() == "world"

    def test_input_context_attached(self) -> None:
        """Test that _input_context is attached to instances."""

        @directed_inputs
        class MyService:
            pass

        svc = MyService()
        assert hasattr(svc, "_input_context")
        assert isinstance(svc._input_context, InputContext)

    def test_from_env_loading(self) -> None:
        """Test loading inputs from environment."""
        with patch.dict(os.environ, {"TEST_DOMAIN": "example.com"}):

            @directed_inputs(from_env=True)
            class MyService:
                def get_domain(self, test_domain: str | None = None) -> str | None:
                    return test_domain

            svc = MyService()
            assert svc.get_domain() == "example.com"

    def test_explicit_kwarg_overrides_env(self) -> None:
        """Test that explicit kwargs override environment values."""
        with patch.dict(os.environ, {"DOMAIN": "from-env.com"}):

            @directed_inputs(from_env=True)
            class MyService:
                def get_domain(self, domain: str | None = None) -> str | None:
                    return domain

            svc = MyService()
            assert svc.get_domain(domain="explicit.com") == "explicit.com"

    def test_default_values(self) -> None:
        """Test that default values work when no input provided."""

        @directed_inputs
        class MyService:
            def get_limit(self, limit: int = 100) -> int:
                return limit

        svc = MyService()
        assert svc.get_limit() == 100

    def test_type_coercion_bool(self) -> None:
        """Test boolean type coercion."""
        with patch.dict(os.environ, {"ENABLED": "true"}):

            @directed_inputs
            class MyService:
                def is_enabled(self, enabled: bool = False) -> bool:
                    return enabled

            svc = MyService()
            assert svc.is_enabled() is True

    def test_type_coercion_int(self) -> None:
        """Test integer type coercion."""
        with patch.dict(os.environ, {"COUNT": "42"}):

            @directed_inputs
            class MyService:
                def get_count(self, count: int = 0) -> int:
                    return count

            svc = MyService()
            assert svc.get_count() == 42

    def test_type_coercion_float(self) -> None:
        """Test float type coercion."""
        with patch.dict(os.environ, {"RATE": "3.14"}):

            @directed_inputs
            class MyService:
                def get_rate(self, rate: float = 0.0) -> float:
                    return rate

            svc = MyService()
            assert svc.get_rate() == 3.14

    def test_direct_inputs_via_constructor(self) -> None:
        """Test passing inputs directly to constructor."""

        @directed_inputs
        class MyService:
            def get_value(self, key: str | None = None) -> str | None:
                return key

        svc = MyService(inputs={"key": "my-value"})
        assert svc.get_value() == "my-value"

    def test_env_prefix_filtering(self) -> None:
        """Test filtering env vars by prefix."""
        with patch.dict(
            os.environ,
            {"APP_DOMAIN": "app.com", "OTHER_DOMAIN": "other.com"},
            clear=True,
        ):

            @directed_inputs(from_env=True, env_prefix="APP_")
            class MyService:
                def get_domain(self, app_domain: str | None = None) -> str | None:
                    return app_domain

            svc = MyService()
            assert svc.get_domain() == "app.com"

    def test_env_prefix_stripping(self) -> None:
        """Test stripping prefix from env var names."""
        with patch.dict(
            os.environ,
            {"APP_DOMAIN": "app.com"},
            clear=True,
        ):

            @directed_inputs(from_env=True, env_prefix="APP_", strip_env_prefix=True)
            class MyService:
                def get_domain(self, domain: str | None = None) -> str | None:
                    return domain

            svc = MyService()
            assert svc.get_domain() == "app.com"

    def test_case_insensitive_lookup(self) -> None:
        """Test that input lookup is case-insensitive."""
        with patch.dict(os.environ, {"DOMAIN": "example.com"}):

            @directed_inputs
            class MyService:
                def get_domain(self, domain: str | None = None) -> str | None:
                    return domain

            svc = MyService()
            assert svc.get_domain() == "example.com"

    def test_stdin_size_limit(self) -> None:
        """Ensure oversized stdin payloads raise a clear error."""

        @directed_inputs(from_stdin=True)
        class MyService:
            def noop(self) -> None:
                return None

        oversized = "x" * (decorators_mod.STDIN_MAX_BYTES + 1)
        with (
            patch(
                "directed_inputs_class.decorators.sys.stdin.read",
                return_value=oversized,
            ),
            pytest.raises(ValueError, match=r"exceeds maximum size"),
        ):
            MyService()


class TestInputConfigDecorator:
    """Tests for @input_config method decorator."""

    def test_source_name_alias(self) -> None:
        """Test using a different source name for input."""
        with patch.dict(os.environ, {"API_DOMAIN": "api.example.com"}):

            @directed_inputs
            class MyService:
                @input_config("domain", source_name="API_DOMAIN")
                def get_domain(self, domain: str | None = None) -> str | None:
                    return domain

            svc = MyService()
            assert svc.get_domain() == "api.example.com"

    def test_required_input_raises(self) -> None:
        """Test that missing required input raises ValueError."""

        @directed_inputs
        class MyService:
            @input_config("domain", required=True)
            def get_domain(self, domain: str) -> str:
                return domain

        svc = MyService()
        with pytest.raises(ValueError, match=r"(?i)required"):
            svc.get_domain()

    def test_default_override(self) -> None:
        """Test overriding default value via decorator."""

        @directed_inputs
        class MyService:
            @input_config("limit", default=500)
            def get_items(self, limit: int = 100) -> int:
                return limit

        svc = MyService()
        # Decorator default should win over parameter default
        assert svc.get_items() == 500

    def test_aliases(self) -> None:
        """Test looking up input by aliases."""
        with patch.dict(os.environ, {"HOSTNAME": "server.local"}):

            @directed_inputs
            class MyService:
                @input_config("host", aliases=["HOSTNAME", "HOST_NAME"])
                def get_host(self, host: str | None = None) -> str | None:
                    return host

            svc = MyService()
            assert svc.get_host() == "server.local"


class TestInputContext:
    """Tests for InputContext class."""

    def test_get_basic(self) -> None:
        """Test basic get operation."""
        ctx = InputContext()
        ctx.inputs["key"] = "value"
        assert ctx.get("key") == "value"

    def test_get_with_default(self) -> None:
        """Test get with default value."""
        ctx = InputContext()
        assert ctx.get("missing", default="default") == "default"

    def test_get_with_aliases(self) -> None:
        """Test get checking aliases."""
        ctx = InputContext()
        ctx.inputs["alternate_key"] = "found"
        assert ctx.get("key", aliases=["alternate_key"]) == "found"

    def test_merge(self) -> None:
        """Test merging new inputs."""
        ctx = InputContext()
        ctx.inputs["a"] = 1
        ctx.merge({"b": 2})
        assert ctx.get("a") == 1
        assert ctx.get("b") == 2

    def test_required_raises(self) -> None:
        """Test that required=True raises on missing."""
        ctx = InputContext()
        with pytest.raises(ValueError, match=r"(?i)required"):
            ctx.get("missing", required=True)


class TestMethodPreservation:
    """Tests that method attributes are preserved."""

    def test_docstring_preserved(self) -> None:
        """Test that method docstrings are preserved."""

        @directed_inputs
        class MyService:
            def documented_method(self) -> None:
                """This is the docstring."""

        assert "docstring" in (MyService.documented_method.__doc__ or "").lower()

    def test_method_name_preserved(self) -> None:
        """Test that method names are preserved."""

        @directed_inputs
        class MyService:
            def my_method(self) -> None:
                pass

        assert MyService.my_method.__name__ == "my_method"
