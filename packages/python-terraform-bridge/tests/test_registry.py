"""Tests for TerraformRegistry."""

from __future__ import annotations

import tempfile

from python_terraform_bridge.registry import TerraformMethodConfig, TerraformRegistry


class TestTerraformMethodConfig:
    """Tests for TerraformMethodConfig."""

    def test_description_from_docstring(self) -> None:
        """Test description extraction from docstring."""

        def my_method() -> dict:
            """This is the description.

            More details here.
            """
            return {}

        config = TerraformMethodConfig(
            method=my_method,
            method_name="my_method",
        )

        assert config.description == "This is the description."

    def test_key_defaults_to_method_name(self) -> None:
        """Test that key defaults to method name."""

        def list_users() -> dict:
            """List users."""
            return {}

        config = TerraformMethodConfig(
            method=list_users,
            method_name="list_users",
        )

        assert config.key == "list_users"

    def test_explicit_key(self) -> None:
        """Test explicit key override."""

        def list_users() -> dict:
            """List users."""
            return {}

        config = TerraformMethodConfig(
            method=list_users,
            method_name="list_users",
            key="users",
        )

        assert config.key == "users"


class TestTerraformRegistry:
    """Tests for TerraformRegistry."""

    def test_register_basic(self) -> None:
        """Test basic method registration."""
        registry = TerraformRegistry()

        @registry.register(key="users")
        def list_users() -> dict:
            """List all users."""
            return {}

        assert "list_users" in registry._methods
        assert registry._methods["list_users"].key == "users"

    def test_data_source_decorator(self) -> None:
        """Test data_source decorator."""
        registry = TerraformRegistry()

        @registry.data_source(key="users", module_class="github")
        def list_users(domain: str | None = None) -> dict:
            """List GitHub users."""
            return {}

        config = registry.get_method("list_users")
        assert config is not None
        assert config.module_type == "data_source"
        assert config.module_class == "github"
        assert config.key == "users"

    def test_null_resource_decorator(self) -> None:
        """Test null_resource decorator."""
        registry = TerraformRegistry()

        @registry.null_resource(module_class="aws")
        def create_bucket(name: str) -> None:
            """Create S3 bucket."""
            pass

        config = registry.get_method("create_bucket")
        assert config is not None
        assert config.module_type == "null_resource"
        assert config.module_class == "aws"

    def test_parameter_inference(self) -> None:
        """Test automatic parameter inference."""
        registry = TerraformRegistry()

        @registry.data_source(key="data")
        def get_data(
            required_str: str,
            optional_str: str = "default",
            number_param: int = 10,
        ) -> dict:
            """Get data."""
            return {}

        config = registry.get_method("get_data")
        assert config is not None

        param_names = {p.name for p in config.parameters}
        assert "required_str" in param_names
        assert "optional_str" in param_names
        assert "number_param" in param_names

        # Check required/optional
        for param in config.parameters:
            if param.name == "required_str":
                assert param.required is True
            elif param.name == "optional_str":
                assert param.required is False
                assert param.default == "default"

    def test_list_methods(self) -> None:
        """Test listing registered methods."""
        registry = TerraformRegistry()

        @registry.data_source(key="users")
        def list_users() -> dict:
            """List all users."""
            return {}

        @registry.data_source(key="groups")
        def list_groups() -> dict:
            """List all groups."""
            return {}

        methods = registry.list_methods()

        assert "list_users" in methods
        assert "list_groups" in methods
        assert methods["list_users"] == "List all users."
        assert methods["list_groups"] == "List all groups."

    def test_generate_modules(self) -> None:
        """Test module generation."""
        import json

        registry = TerraformRegistry()

        @registry.data_source(key="users", module_class="github")
        def list_users(org: str | None = None) -> dict:
            """List GitHub users."""
            return {}

        with tempfile.TemporaryDirectory() as tmpdir:
            generated = registry.generate_modules(output_dir=tmpdir)

            assert "list_users" in generated
            assert generated["list_users"].exists()

            # Check JSON content
            with generated["list_users"].open() as f:
                module_json = json.load(f)

            assert "terraform" in module_json
            assert "variable" in module_json
            assert "data" in module_json

    def test_generation_forbidden(self) -> None:
        """Test that generation_forbidden methods are skipped."""
        registry = TerraformRegistry()

        @registry.data_source(key="users", generation_forbidden=True)
        def internal_users() -> dict:
            """Internal method."""
            return {}

        @registry.data_source(key="groups")
        def list_groups() -> dict:
            """List groups."""
            return {}

        with tempfile.TemporaryDirectory() as tmpdir:
            generated = registry.generate_modules(output_dir=tmpdir)

            assert "internal_users" not in generated
            assert "list_groups" in generated

    def test_to_module_resources(self) -> None:
        """Test conversion to TerraformModuleResources."""
        registry = TerraformRegistry()

        @registry.data_source(key="users", module_class="github")
        def list_users(domain: str | None = None) -> dict:
            """List GitHub users."""
            return {}

        config = registry.get_method("list_users")
        assert config is not None

        resources = config.to_module_resources()

        assert resources.module_name == "list_users"
        assert resources.generator_parameters["key"] == "users"

    def test_wrapper_preserves_function(self) -> None:
        """Test that decorated function still works."""
        registry = TerraformRegistry()

        @registry.data_source(key="result")
        def add_numbers(a: int = 0, b: int = 0) -> dict:
            """Add two numbers."""
            return {"sum": a + b}

        result = add_numbers(a=5, b=3)
        assert result == {"sum": 8}

    def test_multiple_registries(self) -> None:
        """Test multiple independent registries."""
        registry1 = TerraformRegistry("registry1")
        registry2 = TerraformRegistry("registry2")

        @registry1.data_source(key="data1")
        def method1() -> dict:
            """Method 1."""
            return {}

        @registry2.data_source(key="data2")
        def method2() -> dict:
            """Method 2."""
            return {}

        assert "method1" in registry1._methods
        assert "method1" not in registry2._methods
        assert "method2" in registry2._methods
        assert "method2" not in registry1._methods

    def test_get_all_resources(self) -> None:
        """Test getting all resources."""
        registry = TerraformRegistry()

        @registry.data_source(key="users")
        def list_users() -> dict:
            """List users."""
            return {}

        @registry.data_source(key="groups")
        def list_groups() -> dict:
            """List groups."""
            return {}

        resources = registry.get_all_resources()

        assert len(resources) == 2
        names = {r.module_name for r in resources}
        assert "list_users" in names
        assert "list_groups" in names
