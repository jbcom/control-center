
# Directed Inputs Class

![Directed Inputs Class Logo](docs/_static/logo.webp)

*🛠️ Manage your Python inputs efficiently! 🎯*

[![CI Status](https://github.com/jbcom/directed-inputs-class/workflows/CI/badge.svg)](https://github.com/jbcom/directed-inputs-class/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/directed-inputs-class/badge/?version=latest)](https://directed-inputs-class.readthedocs.io/en/latest/?badge=latest)
[![PyPI Package latest release](https://img.shields.io/pypi/v/directed-inputs-class.svg)](https://pypi.org/project/directed-inputs-class/)
[![Supported versions](https://img.shields.io/pypi/pyversions/directed-inputs-class.svg)](https://pypi.org/project/directed-inputs-class/)

Directed Inputs Class is a Python library that provides a flexible and robust interface for managing inputs from various sources such as environment variables, stdin, and predefined dictionaries. It offers features like input freezing, thawing, and advanced decoding utilities.

## Key Features

- 🧩 **Environment Variable Integration** - Seamlessly integrates environment variables into your inputs.
- 🧭 **Scoped Environment Loading** - Filter environment variables by prefix and optionally strip it for clean keys.
- 📥 **Stdin Input Handling** - Read and merge inputs from stdin with optional overrides.
- ❄️ **Input Freezing and Thawing** - Freeze inputs to prevent modifications, and thaw them when needed.
- 🔄 **Advanced Decoding Utilities** - Decode inputs from Base64, JSON, and YAML formats with error handling.
- 🔧 **Type Conversion** - Convert inputs to boolean or integer types with robust error handling.
- 🧬 **Deep Input Merging** - Merge additional inputs into existing state without losing nested structure.

### Example Usage

```python
from directed_inputs_class import DirectedInputsClass

# Initialize with environment variables and stdin
dic = DirectedInputsClass(from_environment=True, from_stdin=True)

# Retrieve and decode an input
decoded_value = dic.decode_input("example_key", decode_from_base64=True)
print(decoded_value)
```

### Freezing and Thawing Inputs

```python
from directed_inputs_class import DirectedInputsClass

# Initialize with some inputs
dic = DirectedInputsClass(inputs={"key1": "value1"})

# Freeze the inputs
frozen_inputs = dic.freeze_inputs()
print(frozen_inputs)  # Outputs: {'key1': 'value1'}

# Thaw the inputs
thawed_inputs = dic.thaw_inputs()
print(thawed_inputs)  # Outputs: {'key1': 'value1'}

# Merge additional data safely
dic.merge_inputs({"feature_flags": {"new": True}})
```

For more usage examples, see the [Usage](https://directed-inputs-class.readthedocs.io/en/latest/usage.md) documentation.

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](https://github.com/jbcom/directed-inputs-class/blob/main/CONTRIBUTING.md) for more information.

## Project Links

- [**Get Help**](https://stackoverflow.com/questions/tagged/directed-inputs-class) (use the *directed-inputs-class* tag on
  Stack Overflow)
- [**PyPI**](https://pypi.org/project/directed-inputs-class/)
- [**GitHub**](https://github.com/jbcom/directed-inputs-class)
- [**Documentation**](https://directed-inputs-class.readthedocs.io/en/latest/)
- [**Changelog**](https://github.com/jbcom/directed-inputs-class/tree/main/CHANGELOG.md)
