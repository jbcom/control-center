"""Tests for TerraformModuleResources."""

from __future__ import annotations

from pathlib import Path

from python_terraform_bridge.module_resources import TerraformModuleResources


class TestTerraformModuleResources:
    """Tests for TerraformModuleResources class."""

    def test_basic_data_source(self) -> None:
        """Test basic data source module generation."""
        docstring = """List all users.

        generator=key: users, type: data_source

        name: domain, required: false, type: string
        """

        resources = TerraformModuleResources(
            module_name="list_users",
            docstring=docstring,
        )

        assert resources.module_name == "list_users"
        assert resources.descriptor == "List all users."
        assert not resources.generation_forbidden

    def test_generator_parameters_parsing(self) -> None:
        """Test parsing of generator parameters."""
        docstring = """Get data.

        generator=key: output, type: data_source, module_class: myservice, plaintext_output: true
        """

        resources = TerraformModuleResources(
            module_name="get_data",
            docstring=docstring,
        )

        assert resources.generator_parameters["key"] == "output"
        assert resources.generator_parameters["type"] == "data_source"
        assert resources.generator_parameters["module_class"] == "myservice"
        assert resources.generator_parameters["plaintext_output"] is True

    def test_parameter_parsing(self) -> None:
        """Test parsing of parameter definitions."""
        docstring = """Get users.

        generator=key: users

        name: domain, required: true, type: string, description: "Target domain"
        name: limit, required: false, type: number, default: 100
        """

        resources = TerraformModuleResources(
            module_name="get_users",
            docstring=docstring,
        )

        # Should have domain, limit, and checksum (auto-added)
        param_names = {p.name for p in resources.module_parameters}
        assert "domain" in param_names
        assert "limit" in param_names
        assert "checksum" in param_names

    def test_noterraform_comment(self) -> None:
        """Test that #NOTERRAFORM disables generation."""
        docstring = """Internal method.

        # NOTERRAFORM
        """

        resources = TerraformModuleResources(
            module_name="internal_method",
            docstring=docstring,
        )

        assert resources.generation_forbidden is True

    def test_env_variable_parsing(self) -> None:
        """Test parsing of environment variables."""
        docstring = """Get data.

        generator=key: data

        env=name: GITHUB_TOKEN, required: true
        env=name: API_SECRET, required: true, sensitive: true
        """

        resources = TerraformModuleResources(
            module_name="get_data",
            docstring=docstring,
        )

        assert "GITHUB_TOKEN" in resources.env_variables
        assert "API_SECRET" in resources.sensitive_env_variables

    def test_get_external_data(self) -> None:
        """Test external_data module generation."""
        docstring = """List users.

        generator=key: users

        name: domain, required: false, type: string
        """

        resources = TerraformModuleResources(
            module_name="list_users",
            docstring=docstring,
        )

        module_json = resources.get_external_data()

        # Check structure
        assert "terraform" in module_json
        assert "variable" in module_json
        assert "data" in module_json
        assert "locals" in module_json
        assert "output" in module_json

        # Check terraform block
        assert "required_providers" in module_json["terraform"]
        assert "external" in module_json["terraform"]["required_providers"]

        # Check data block
        assert "external" in module_json["data"]
        assert "default" in module_json["data"]["external"]

        # Check output
        assert "users" in module_json["output"]

    def test_get_null_resource(self) -> None:
        """Test null_resource module generation."""
        docstring = """Update something.

        generator=type: null_resource

        name: target, required: true, type: string
        """

        resources = TerraformModuleResources(
            module_name="update_target",
            docstring=docstring,
        )

        module_json = resources.get_null_resource()

        # Check structure
        assert "terraform" in module_json
        assert "variable" in module_json
        assert "resource" in module_json

        # Check resource block
        assert "terraform_data" in module_json["resource"]
        assert "default" in module_json["resource"]["terraform_data"]

        # Check provisioner
        resource = module_json["resource"]["terraform_data"]["default"]
        assert "triggers_replace" in resource
        assert "provisioner" in resource

    def test_get_mixed_data_source(self) -> None:
        """Test get_mixed for data_source type."""
        docstring = """List items.

        generator=key: items, type: data_source
        """

        resources = TerraformModuleResources(
            module_name="list_items",
            docstring=docstring,
        )

        module_json = resources.get_mixed()

        # Should be external data format
        assert "data" in module_json
        assert "external" in module_json["data"]

    def test_get_mixed_null_resource(self) -> None:
        """Test get_mixed for null_resource type."""
        docstring = """Create item.

        generator=type: null_resource
        """

        resources = TerraformModuleResources(
            module_name="create_item",
            docstring=docstring,
        )

        module_json = resources.get_mixed()

        # Should be terraform_data format
        assert "resource" in module_json
        assert "terraform_data" in module_json["resource"]

    def test_get_module_path(self) -> None:
        """Test module path generation."""
        docstring = """Get data.

        generator=key: data, module_class: aws
        """

        resources = TerraformModuleResources(
            module_name="get_data",
            docstring=docstring,
            terraform_modules_dir="modules",
        )

        path = resources.get_module_path()

        assert isinstance(path, Path)
        assert "aws" in str(path)
        assert "get-data" in str(path) or "get_data" in str(path)
        assert path.name == "main.tf.json"

    def test_get_module_name(self) -> None:
        """Test module name generation."""
        resources = TerraformModuleResources(
            module_name="list_users",
            docstring="Test.\n\ngenerator=key: users, module_class: github",
        )

        name = resources.get_module_name()

        # Should combine class and name with delimiter
        assert "github" in name
        assert "list" in name
        assert "users" in name

    def test_plaintext_output(self) -> None:
        """Test plaintext output mode."""
        docstring = """Get status.

        generator=key: status, plaintext_output: true
        """

        resources = TerraformModuleResources(
            module_name="get_status",
            docstring=docstring,
        )

        module_json = resources.get_external_data()

        # Plaintext output should not use jsondecode/base64decode
        locals_block = module_json["locals"]
        results = locals_block["results"]
        assert "jsondecode" not in results
        assert "base64decode" not in results

    def test_always_run(self) -> None:
        """Test always run trigger."""
        docstring = """Get timestamp.

        generator=key: time, always: true

        name: zone, required: false, type: string
        """

        resources = TerraformModuleResources(
            module_name="get_timestamp",
            docstring=docstring,
        )

        triggers = resources.get_triggers()

        assert "always" in triggers
        assert "timestamp()" in triggers["always"]

    def test_extra_outputs(self) -> None:
        """Test extra output definitions."""
        docstring = """Get data with multiple outputs.

        generator=key: primary

        extra_output=key: secondary
        extra_output=key: tertiary
        """

        resources = TerraformModuleResources(
            module_name="get_multi",
            docstring=docstring,
        )

        module_json = resources.get_external_data()

        # Should have all outputs
        assert "primary" in module_json["output"]
        assert "secondary" in module_json["output"]
        assert "tertiary" in module_json["output"]

    def test_required_providers(self) -> None:
        """Test required provider definitions.

        Note: Values containing special characters like / must be quoted.
        """
        docstring = """Get from AWS.

        generator=key: data

        required_provider=name: aws, source: "hashicorp/aws", version: ">=5.0"
        """

        resources = TerraformModuleResources(
            module_name="get_aws_data",
            docstring=docstring,
        )

        module_json = resources.get_external_data()

        providers = module_json["terraform"]["required_providers"]
        assert "aws" in providers
        assert providers["aws"]["source"] == "hashicorp/aws"

    def test_binary_name_customization(self) -> None:
        """Test custom binary name."""
        resources = TerraformModuleResources(
            module_name="test",
            docstring="Test.\n\ngenerator=key: test",
            binary_name="terraform-modules",
        )

        assert resources.binary_name == "terraform-modules"
        assert resources.call == "terraform-modules test"

    def test_external_data_program_is_tokenized(self) -> None:
        """Program list should preserve python -m arguments safely."""

        resources = TerraformModuleResources(
            module_name="list_users",
            docstring="Doc.\n\ngenerator=key: users",
        )

        module_json = resources.get_external_data()
        program = module_json["data"]["external"]["default"]["program"]

        assert program == ["python", "-m", "python_terraform_bridge", "list_users"]

    def test_command_string_is_shell_safe(self) -> None:
        """Ensure command injection via method name is mitigated."""

        resources = TerraformModuleResources(
            module_name="dangerous; rm -rf /",
            docstring="Doc.\n\ngenerator=key: data",
        )

        assert resources.call.endswith("'dangerous; rm -rf /'")

    def test_empty_docstring(self) -> None:
        """Test handling of empty docstring."""
        resources = TerraformModuleResources(
            module_name="no_docs",
            docstring=None,
        )

        # Should not raise, just have minimal config
        assert resources.module_name == "no_docs"
        assert resources.descriptor is None

    def test_get_variables(self) -> None:
        """Test variable block generation."""
        docstring = """Get data.

        generator=key: data

        name: required_param, required: true, type: string
        name: optional_param, required: false, type: string, default: "test"
        name: sensitive_param, required: true, type: string, sensitive: true
        """

        resources = TerraformModuleResources(
            module_name="get_data",
            docstring=docstring,
        )

        variables = resources.get_variables()

        assert "required_param" in variables
        assert "optional_param" in variables
        assert "sensitive_param" in variables

        # Check required has no default
        assert "default" not in variables["required_param"]

        # Check optional has default
        assert variables["optional_param"]["default"] == "test"

        # Check sensitive flag
        assert variables["sensitive_param"]["sensitive"] is True
