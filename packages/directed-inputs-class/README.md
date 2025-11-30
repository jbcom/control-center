# Directed Inputs Class

![Directed Inputs Class Logo](docs/_static/logo.webp)

*🛠️ Manage your Python inputs efficiently! 🎯*

[![CI Status](https://github.com/jbcom/directed-inputs-class/workflows/CI/badge.svg)](https://github.com/jbcom/directed-inputs-class/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/directed-inputs-class/badge/?version=latest)](https://directed-inputs-class.readthedocs.io/en/latest/?badge=latest)
[![PyPI Package latest release](https://img.shields.io/pypi/v/directed-inputs-class.svg)](https://pypi.org/project/directed-inputs-class/)
[![Supported versions](https://img.shields.io/pypi/pyversions/directed-inputs-class.svg)](https://pypi.org/project/directed-inputs-class/)

Directed Inputs Class provides flexible, transparent input handling for Python applications. Load inputs from environment variables, stdin, or dictionaries and have them automatically injected into your method arguments.

## Key Features

- 🎯 **Decorator-Based API** - No inheritance required, use `@directed_inputs` on any class
- 🧩 **Automatic Type Coercion** - String inputs converted to `bool`, `int`, `float`, `datetime`, `Path`
- 📥 **Multi-Source Loading** - Environment variables, stdin JSON, or predefined dictionaries
- 🧭 **Scoped Environment Loading** - Filter by prefix with optional stripping
- 🔄 **Advanced Decoding** - Base64, JSON, and YAML decoding with error handling
- ❄️ **Input Freezing/Thawing** - Immutable snapshots with restore capability
- 🔧 **Per-Method Configuration** - Use `@input_config` for custom parameter handling

---

## Quick Start

### Installation

```bash
pip install directed-inputs-class
```

### Decorator API (Recommended)

The decorator API provides transparent input handling without inheritance:

```python
from directed_inputs_class import directed_inputs, input_config

@directed_inputs(from_stdin=True, from_env=True)
class MyService:
    """Methods automatically receive inputs from stdin/environment."""
    
    def list_users(self, domain: str | None = None, limit: int = 100) -> list:
        # 'domain' and 'limit' are automatically populated from:
        # 1. Stdin JSON (if from_stdin=True)
        # 2. Environment variables (if from_env=True)
        # 3. Default values (if not found)
        return self._fetch_users(domain, limit)
    
    @input_config("api_key", source_name="API_KEY", required=True)
    def secure_operation(self, api_key: str, data: dict) -> dict:
        # 'api_key' MUST be provided (from env var API_KEY)
        # 'data' is loaded normally
        return self._process(api_key, data)

# Usage
service = MyService()
result = service.list_users()  # domain/limit loaded automatically
```

### Input Resolution Order

For each method parameter, inputs are resolved in this order:

1. **Explicit argument** - `service.method(domain="example.com")` always wins
2. **Stdin JSON** - If `from_stdin=True` and key matches parameter name
3. **Environment variable** - If `from_env=True` (checks `DOMAIN` or `env_prefix + DOMAIN`)
4. **Default value** - Falls back to parameter default

---

## Decorator Reference

### `@directed_inputs`

Class decorator that enables automatic input handling for all methods:

```python
@directed_inputs(
    from_stdin=False,      # Read JSON from stdin on first method call
    from_env=True,         # Load matching environment variables
    env_prefix=None,       # Filter env vars by prefix (e.g., "MY_APP_")
    strip_env_prefix=False # Strip prefix from keys (MY_APP_FOO → FOO)
)
class MyService:
    ...
```

### `@input_config`

Method decorator for per-parameter configuration:

```python
@input_config(
    "param_name",          # Parameter to configure
    source_name=None,      # Alternative source name (e.g., "API_KEY" → api_key param)
    aliases=None,          # List of alternative names to check
    required=False,        # Raise error if not found
    default=None,          # Override default value
    decode_base64=False,   # Decode value from base64
    decode_json=False,     # Parse value as JSON
    decode_yaml=False,     # Parse value as YAML
)
def method(self, param_name: str):
    ...
```

### `InputContext`

Access the input context directly:

```python
@directed_inputs
class MyService:
    def debug(self):
        # Access raw inputs
        ctx = self._input_context
        print(f"All inputs: {ctx.inputs}")
        print(f"Frozen: {ctx.frozen}")
        
        # Manual input retrieval
        value = ctx.get("key", default="fallback")
```

---

## Type Coercion

String inputs from environment/stdin are automatically coerced based on type hints:

| Type Hint | Coercion |
|-----------|----------|
| `bool` | `"true"/"1"/"yes"` → `True`, `"false"/"0"/"no"` → `False` |
| `int` | `"42"` → `42` |
| `float` | `"3.14"` → `3.14` |
| `Path` | `"/tmp/file"` → `Path("/tmp/file")` |
| `datetime` | ISO format string → `datetime` object |
| `dict` | JSON string → parsed dict |
| `list` | JSON string → parsed list |
| `str \| None` | Handles Optional types correctly |

Example:

```python
import os
from directed_inputs_class import directed_inputs

os.environ["DEBUG"] = "true"
os.environ["PORT"] = "8080"

@directed_inputs
class Config:
    def get_settings(self, debug: bool = False, port: int = 3000) -> dict:
        return {"debug": debug, "port": port}

config = Config()
print(config.get_settings())  # {"debug": True, "port": 8080}
```

---

## Advanced Examples

### Required Parameters

```python
from directed_inputs_class import directed_inputs, input_config

@directed_inputs
class SecureService:
    @input_config("api_key", required=True)
    def call_api(self, api_key: str, endpoint: str) -> dict:
        # Raises ValueError if api_key not in env/stdin
        ...
```

### Base64 Decoding

```python
import os
import base64
from directed_inputs_class import directed_inputs, input_config

# Set encoded value
os.environ["CERT"] = base64.b64encode(b"certificate-data").decode()

@directed_inputs
class TLSClient:
    @input_config("cert", decode_base64=True)
    def connect(self, cert: str) -> None:
        # cert is automatically decoded from base64
        print(cert)  # "certificate-data"
```

### Environment Prefix

```python
import os
from directed_inputs_class import directed_inputs

os.environ["MY_APP_DATABASE_URL"] = "postgres://..."
os.environ["MY_APP_DEBUG"] = "true"
os.environ["OTHER_VAR"] = "ignored"

@directed_inputs(env_prefix="MY_APP_", strip_env_prefix=True)
class AppConfig:
    def get_db(self, database_url: str | None = None) -> str:
        # Only MY_APP_* variables loaded
        # Prefix stripped: MY_APP_DATABASE_URL → DATABASE_URL
        return database_url
```

### Stdin JSON Input

```bash
echo '{"user": "alice", "count": 5}' | python script.py
```

```python
from directed_inputs_class import directed_inputs

@directed_inputs(from_stdin=True)
class Processor:
    def process(self, user: str, count: int = 10) -> str:
        return f"Processing {count} items for {user}"

p = Processor()
print(p.process())  # "Processing 5 items for alice"
```

---

## Legacy API (DirectedInputsClass)

The original inheritance-based API is still supported for backward compatibility:

```python
from directed_inputs_class import DirectedInputsClass

class MyService(DirectedInputsClass):
    def __init__(self):
        super().__init__(from_environment=True, from_stdin=True)
    
    def get_user(self, user_id: str | None = None) -> dict:
        user_id = self.get_input("user_id", user_id)
        return self._fetch_user(user_id)
```

### Legacy Methods

| Method | Purpose |
|--------|---------|
| `get_input(name, default)` | Get input with fallback |
| `decode_input(name, ...)` | Get and decode (base64/json/yaml) |
| `freeze_inputs()` | Get immutable snapshot |
| `thaw_inputs()` | Restore from frozen state |
| `merge_inputs(dict)` | Deep merge additional inputs |

### Migration to Decorator API

```python
# Before (inheritance + manual get_input)
class OldService(DirectedInputsClass):
    def method(self, domain: str | None = None):
        domain = self.get_input("domain", domain)
        return self._process(domain)

# After (decorator + automatic injection)
@directed_inputs
class NewService:
    def method(self, domain: str | None = None):
        return self._process(domain)
```

---

## Integration with python-terraform-bridge

The decorator API integrates seamlessly with [python-terraform-bridge](https://github.com/jbcom/jbcom-control-center/tree/main/packages/python-terraform-bridge) for Terraform external data sources:

```python
from directed_inputs_class import directed_inputs
from python_terraform_bridge import TerraformRegistry

registry = TerraformRegistry()

@directed_inputs(from_stdin=True)  # Terraform passes inputs via stdin
class GitHubConnector:
    
    @registry.data_source(key="repos", module_class="github")
    def list_repos(self, org: str, include_private: bool = True) -> dict:
        # Both decorators compose naturally:
        # - @directed_inputs handles input loading from Terraform's stdin
        # - @registry.data_source handles Terraform module generation
        return {"repos": [...]}
```

---

## API Reference

### Exports

```python
from directed_inputs_class import (
    # Decorator API (recommended)
    directed_inputs,    # Class decorator
    input_config,       # Method decorator
    InputConfig,        # Configuration dataclass
    InputContext,       # Runtime context
    
    # Legacy API (backward compatible)
    DirectedInputsClass,
)
```

### InputConfig Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | required | Parameter name |
| `source_name` | `str \| None` | `None` | Alternative env var name |
| `aliases` | `list[str]` | `[]` | Alternative names to check |
| `required` | `bool` | `False` | Raise if not found |
| `default` | `Any` | `None` | Override default |
| `decode_base64` | `bool` | `False` | Decode from base64 |
| `decode_json` | `bool` | `False` | Parse as JSON |
| `decode_yaml` | `bool` | `False` | Parse as YAML |

---

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](https://github.com/jbcom/directed-inputs-class/blob/main/CONTRIBUTING.md) for more information.

## Project Links

- [**Get Help**](https://stackoverflow.com/questions/tagged/directed-inputs-class) (use the *directed-inputs-class* tag)
- [**PyPI**](https://pypi.org/project/directed-inputs-class/)
- [**GitHub**](https://github.com/jbcom/directed-inputs-class)
- [**Documentation**](https://directed-inputs-class.readthedocs.io/en/latest/)
- [**Changelog**](https://github.com/jbcom/directed-inputs-class/tree/main/CHANGELOG.md)
