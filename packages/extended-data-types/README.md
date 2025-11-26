# Extended Data Types

[![Extended Data Types Logo](docs/_static/logo.png)](https://github.com/jbcom/extended-data-types)

*🐍 Supercharge your Python data types! 🚀*

[![CI Status](https://github.com/jbcom/extended-data-types/workflows/CI/badge.svg)](https://github.com/jbcom/extended-data-types/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/extended-data-types/badge/?version=latest)](https://extended-data-types.readthedocs.io/en/latest/?badge=latest)
[![PyPI Package latest release](https://img.shields.io/pypi/v/extended-data-types.svg)](https://pypi.org/project/extended-data-types/)
[![Supported versions](https://img.shields.io/pypi/pyversions/extended-data-types.svg)](https://pypi.org/project/extended-data-types/)

Extended Data Types is a Python library that provides additional functionality for Python's standard data types. It includes utilities for handling YAML, JSON, Base64, file paths, strings, lists, maps, and more.

## Project Goals

- Provide a reliable, typed utility layer for working with common serialization formats (YAML, JSON, TOML, HCL) without sacrificing readability or ergonomics.
- Offer safe helpers for file-system aware workflows, including path handling and Git repository discovery, while keeping platform differences in mind.
- Maintain a modern, well-tested codebase backed by automated CI/CD that validates packaging, linting, typing, coverage, and documentation builds.

## Key Features

- 🔒 **Base64 encoding and decoding** - Easily encode data to Base64 format with optional wrapping for export.
- 📁 **File path utilities** - Manipulate and validate file paths, check file extensions, and determine encoding types.
- 🗺️ **Extended map and list utilities** - Flatten, filter, and manipulate dictionaries and lists with ease.
- 🔍 **String matching and manipulation** - Partially match strings, convert case, and validate URLs.
- 🎛️ **Custom YAML utilities** - Handle custom YAML tags, construct YAML pairs, and represent data structures.

### Base64 Encoding

```
from extended_data_types import base64_encode

data = "Hello, world!"
encoded = base64_encode(data)
print(encoded)  # Output: SGVsbG8sIHdvcmxkIQ==
```

### File Path Utilities

```python
from extended_data_types import match_file_extensions

file_path = "example.txt"
allowed_extensions = [".txt", ".log"]
is_allowed = match_file_extensions(file_path, allowed_extensions)
print(is_allowed)  # Output: True
```

### YAML Utilities

```python
from extended_data_types import encode_yaml, decode_yaml

data = {"name": "Alice", "age": 30}
yaml_str = encode_yaml(data)
print(yaml_str)
# Output:
# name: Alice
# age: 30

decoded_data = decode_yaml(yaml_str)
print(decoded_data)  # Output: {'name': 'Alice', 'age': 30}
```

For more usage examples, see the [Usage](https://extended-data-types.readthedocs.io/en/latest/usage.md) documentation.

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](https://github.com/jbcom/extended-data-types/blob/main/CONTRIBUTING.md) for more information.

## Credit

Extended Data Types is written and maintained by [Jon Bogaty](mailto:jon@jonbogaty.com).

## Project Links

- [**Get Help**](https://stackoverflow.com/questions/tagged/extended-data-types) (use the *extended-data-types* tag on
  Stack Overflow)
- [**PyPI**](https://pypi.org/project/extended-data-types/)
- [**GitHub**](https://github.com/jbcom/extended-data-types)
- [**Documentation**](https://extended-data-types.readthedocs.io/en/latest/)
- [**Changelog**](https://github.com/jbcom/extended-data-types/tree/main/CHANGELOG.md)
