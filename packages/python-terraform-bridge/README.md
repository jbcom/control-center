# python-terraform-bridge

Bridge Python classes to Terraform external data sources and modules.

## Overview

`python-terraform-bridge` provides a framework for:

1. **Generating Terraform modules** from Python `DirectedInputsClass` methods
2. **Running as a Terraform external data provider** via stdin/stdout
3. **Decorator-based registration** as an alternative to docstring parsing

This package extracts and generalizes the Terraform integration layer from specific implementations, making it reusable for any Python codebase.

## Installation

```bash
pip install python-terraform-bridge
```

Or with development dependencies:

```bash
pip install "python-terraform-bridge[dev]"
```

## Quick Start

### Decorator-Based Registration (Recommended)

```python
from directed_inputs_class import DirectedInputsClass
from python_terraform_bridge import TerraformRegistry, data_source

registry = TerraformRegistry()

class MyConnector(DirectedInputsClass):
    @registry.data_source(key="users", module_class="myservice")
    def list_users(self, domain: str = None) -> dict:
        """List all users in the organization."""
        return {"user1": {"name": "Alice"}, "user2": {"name": "Bob"}}

    @registry.data_source(key="groups", module_class="myservice")
    def list_groups(self, type_filter: str = "all") -> dict:
        """List all groups."""
        return {"admins": {...}, "users": {...}}

# Generate Terraform modules
registry.generate_modules("./terraform-modules")
```

This generates:
```
terraform-modules/
├── myservice/
│   ├── myservice-list-users/
│   │   └── main.tf.json
│   └── myservice-list-groups/
│       └── main.tf.json
```

### Docstring-Based Configuration (Legacy/Compatible)

```python
class MyDataSource(DirectedInputsClass):
    def list_users(self, domain: str = None) -> dict:
        """List all users.

        generator=key: users, type: data_source, module_class: myservice

        name: domain, required: false, type: string, description: "Domain filter"
        """
        return {"user1": {...}}
```

### Running as External Data Provider

```bash
# Generate modules
terraform-bridge generate mypackage:MyDataSource -o ./terraform-modules

# Run directly (Terraform calls this)
echo '{"domain": "example.com"}' | python -m python_terraform_bridge run mypackage:MyDataSource list_users
```

### Using Generated Modules in Terraform

```hcl
module "users" {
  source = "./terraform-modules/myservice/myservice-list-users"

  domain = "example.com"
}

output "user_list" {
  value = module.users.users
}
```

## CLI Reference

```bash
# Generate Terraform modules
terraform-bridge generate <module:Class> [options]
  -o, --output        Output directory (default: terraform-modules)
  -c, --module-class  Module class prefix
  -b, --binary        Runtime invocation command

# List available methods
terraform-bridge list <module:Class> [--json]

# Run as external data provider
terraform-bridge run <module:Class> <method_name>
```

## API Reference

### TerraformRegistry

```python
registry = TerraformRegistry(name="myregistry")

# Register as data source
@registry.data_source(
    key="output_key",           # Output key name
    module_class="namespace",   # Module prefix
    description="...",          # Override docstring
    parameters=[...],           # Explicit parameters
    env_variables={...},        # Environment variables to read
    always_run=False,           # Always trigger execution
    plaintext_output=False,     # Output plaintext vs base64 JSON
)
def my_method(...): ...

# Register as null_resource (for side effects)
@registry.null_resource(module_class="namespace")
def my_action(...): ...

# Generate all modules
registry.generate_modules("./output")
```

### TerraformModuleResources

Low-level module generation:

```python
from python_terraform_bridge import TerraformModuleResources

resources = TerraformModuleResources(
    module_name="list_users",
    docstring=my_method.__doc__,
    terraform_modules_dir="./modules",
    terraform_modules_class="myservice",
)

# Get as external_data module
module_json = resources.get_external_data(key="users")

# Get as null_resource module
module_json = resources.get_null_resource()

# Get based on docstring configuration
module_json = resources.get_mixed()
```

### TerraformRuntime

For programmatic invocation:

```python
from python_terraform_bridge import TerraformRuntime

runtime = TerraformRuntime(
    data_source_class=MyDataSource,
    null_resource_class=MyActions,
)

# Invoke directly
result = runtime.invoke("list_users", domain="example.com")

# Run as CLI
runtime.run()
```

### Lambda Handler Factory

For AWS Lambda:

```python
from python_terraform_bridge.runtime import lambda_handler_factory

handler = lambda_handler_factory(MyDataSource)

# Lambda event:
# {"method": "list_users", "kwargs": {"domain": "example.com"}}
```

## Docstring Format

Parameters are defined per line:

```python
"""Short description.

generator=key: output_key, type: data_source, module_class: prefix

name: param_name, type: string, required: true, description: "..."
name: optional_param, type: string, required: false, default: "value"
name: sensitive_param, type: string, sensitive: true

env=name: MY_TOKEN, required: true, sensitive: true

extra_output=key: secondary_output
sub_key=key: nested_value, json_encode: true
"""
```

### Generator Parameters

- `key`: Output key name (required)
- `type`: `data_source` or `null_resource`
- `module_class`: Module namespace prefix
- `plaintext_output`: `true` to skip base64 encoding
- `always`: `true` to always trigger

### Parameter Types

- `string`, `bool`, `number`, `any`
- `list(any)`, `map(any)`
- Auto-inferred from Python type hints

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Application                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ DirectedInputs  │  │   vendor-       │  │  Your Custom   │  │
│  │     Class       │  │   connectors    │  │    Classes     │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
└───────────┼─────────────────────┼──────────────────┼────────────┘
            │                     │                  │
            v                     v                  v
┌─────────────────────────────────────────────────────────────────┐
│                   python-terraform-bridge                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Registry    │  │  Module      │  │  Runtime             │  │
│  │  (decorators)│  │  Resources   │  │  (stdin/stdout)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │                     │                  │
            v                     v                  v
┌─────────────────────────────────────────────────────────────────┐
│                       Terraform                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  module "users" {                                          │ │
│  │    source = "./terraform-modules/myservice/list-users"     │ │
│  │    domain = "example.com"                                  │ │
│  │  }                                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Contributing

This package is part of the jbcom-control-center monorepo.

```bash
# Run tests
pytest packages/python-terraform-bridge/tests/

# Lint
ruff check packages/python-terraform-bridge/
ruff format packages/python-terraform-bridge/
```

## License

MIT License - see [LICENSE](../../LICENSE) for details.
