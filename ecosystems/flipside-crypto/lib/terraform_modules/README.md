# Terraform Modules Library

This directory contains the Python library that powers the dynamic Terraform module generation system for this repository.

## Overview

The terraform_modules library enables the creation of dynamic Terraform modules by defining Python functions that get automatically converted into Terraform modules using the `tm_cli` command. This approach allows for complex data processing, API integrations, and business logic to be implemented in Python while providing a clean Terraform interface.

## Architecture

### Core Components

- **`terraform_data_source.py`**: Main class containing all the data source functions that get converted to Terraform modules
- **`utils.py`**: Utility functions and base classes
- **Supporting modules**: Various client classes for AWS, Google, GitHub, Slack, Vault, etc.

### How It Works

1. **Function Definition**: Python functions are defined in `TerraformDataSource` class with special docstring annotations
2. **Module Generation**: Running `tm_cli terraform_modules` processes these functions and generates corresponding Terraform modules
3. **Module Usage**: Generated modules can be used in Terraform configurations with proper inputs/outputs

### Function Annotations

Functions intended to become Terraform modules use special docstring annotations:

```python
def my_function(
        self,
        param1: Optional[str] = None,
        param2: Optional[dict[str, Any]] = None,
        exit_on_completion: bool = True,
):
    """Function description
    
    generator=key: output_key, module_class: category_name
    
    name: param1, required: true, type: string
    name: param2, required: false, default: {}, json_encode: true, base64_encode: true
    """
```

#### Annotation Parameters

- **`generator`**: Defines the output key and module class (category)
- **`name`**: Defines input variables with their types, requirements, and encoding options
- **`plaintext_output`**: For simple string outputs
- **`no_class_in_module_name`**: Excludes class name from generated module name
- **`foreach`**: For modules that support for_each iteration

#### Input Parameter Options

- **`required`**: Whether the parameter is required (true/false)
- **`type`**: Parameter type (string, number, bool, etc.)
- **`default`**: Default value
- **`json_encode`**: Whether to JSON encode the input
- **`base64_encode`**: Whether to base64 encode the input
- **`foreach_only`**: Parameter only available in foreach mode
- **`foreach_iterator`**: The iterable parameter for foreach
- **`foreach_key`**: The key parameter for foreach

## Adding New Functions

### Step 1: Define the Function

Add your function to the `TerraformDataSource` class in `terraform_data_source.py`:

```python
def process_nested_vendor_params(
        self,
        vendor_params: Optional[Any] = None,
        exit_on_completion: bool = True,
):
    """Processes nested vendor parameters, recursively replacing string values with interpolated vendor references

    generator=key: processed_params, module_class: utils

    name: vendor_params, required: true, json_encode: true, base64_encode: true
    """
    if vendor_params is None:
        vendor_params = self.decode_input("vendor_params", required=True, allow_none=False)

    # Your processing logic here
    processed_params = process_logic(vendor_params)

    return self.exit_run(
        results=processed_params,
        key="processed_params",
        encode_to_base64=True,
        format_json=False,
        exit_on_completion=exit_on_completion,
    )
```

### Step 2: Generate the Module

Run the module generation command:

```bash
tm_cli terraform_modules
```

This will create a new Terraform module in the appropriate category directory (e.g., `utils/utils-process-nested-vendor-params/`).

### Step 3: Use the Module

The generated module can now be used in Terraform configurations:

```hcl
module "process_vendor_params" {
  source = "../../utils/utils-process-nested-vendor-params"
  
  vendor_params = {
    auth_login = {
      path = "HCP_VAULT_APPROLE_ROLE_PATH"
      parameters = {
        role_id = "HCP_VAULT_APPROLE_ROLE_ID"
        secret_id = "HCP_VAULT_APPROLE_SECRET_ID"
      }
    }
  }
}

# Access the output
locals {
  processed_config = module.process_vendor_params.processed_params
}
```

## Input/Output Handling

### Input Processing

- **`get_input()`**: Retrieves simple string/number/boolean inputs
- **`decode_input()`**: Retrieves and decodes JSON/base64 encoded inputs
- **Input validation**: Automatic type checking and requirement validation

### Output Generation

- **`exit_run()`**: Standard output method with encoding options
- **`encode_to_base64`**: Whether to base64 encode the output
- **`format_json`**: Whether to format JSON output
- **`key`**: The output key name in the generated module

## Common Patterns

### Data Source Pattern
Functions that fetch data from external APIs or services:

```python
def get_external_data(self, api_endpoint: str, exit_on_completion: bool = True):
    """Gets data from external API
    
    generator=key: data, module_class: external
    
    name: api_endpoint, required: true, type: string
    """
    # Fetch and process data
    return self.exit_run(results=data, key="data", exit_on_completion=exit_on_completion)
```

### Processing Pattern
Functions that transform or process input data:

```python
def process_data(self, input_data: dict, exit_on_completion: bool = True):
    """Processes input data
    
    generator=key: processed_data, module_class: utils
    
    name: input_data, required: true, json_encode: true, base64_encode: true
    """
    # Transform data
    return self.exit_run(results=processed_data, key="processed_data", exit_on_completion=exit_on_completion)
```

### For-Each Pattern
Functions that support iteration over multiple items:

```python
def process_items(self, items: dict, item: dict, exit_on_completion: bool = True):
    """Processes individual items
    
    generator=key: result, module_class: utils
    foreach=module_name: process_multiple_items
    
    name: items, required: true, foreach_only: true, foreach_iterator: true, json_encode: true
    name: item, required: true, foreach_value: true, json_encode: true
    """
    # Process single item
    return self.exit_run(results=result, key="result", exit_on_completion=exit_on_completion)
```

## Best Practices

1. **Error Handling**: Use `self.errors.append()` to collect errors, handle exceptions gracefully
2. **Logging**: Use `self.logger` for consistent logging throughout the function
3. **Input Validation**: Always validate inputs and provide meaningful error messages  
4. **Output Consistency**: Use consistent output keys and encoding patterns
5. **Documentation**: Provide clear function descriptions and parameter documentation
6. **Type Handling**: Handle JSON strings, base64 encoding, and mixed data types properly

## Module Categories

Generated modules are organized into categories based on their `module_class`:

- **`aws`**: AWS-related modules
- **`google`**: Google Cloud Platform modules  
- **`github`**: GitHub integration modules
- **`utils`**: Utility and processing modules
- **`vault`**: HashiCorp Vault modules
- **`slack`**: Slack integration modules
- **`gitops`**: GitOps workflow modules
- **`terraform`**: Terraform state and configuration modules

## Testing and Validation

After adding new functions:

1. Run `tm_cli terraform_modules` to generate modules
2. Test the generated modules in a Terraform configuration
3. Validate inputs/outputs match expectations
4. Ensure error handling works correctly
5. Check that logging provides useful information

## Example: Nested Vendor Parameter Processing

The `process_nested_vendor_params` function demonstrates processing complex nested data structures:

**Input**:
```json
{
  "auth_login": {
    "path": "HCP_VAULT_APPROLE_ROLE_PATH",
    "parameters": {
      "role_id": "HCP_VAULT_APPROLE_ROLE_ID", 
      "secret_id": "HCP_VAULT_APPROLE_SECRET_ID"
    }
  }
}
```

**Output**:
```json
{
  "auth_login": {
    "path": "${local.vendors_data.HCP_VAULT_APPROLE_ROLE_PATH}",
    "parameters": {
      "role_id": "${local.vendors_data.HCP_VAULT_APPROLE_ROLE_ID}",
      "secret_id": "${local.vendors_data.HCP_VAULT_APPROLE_SECRET_ID}"
    }
  }
}
```

This enables Terraform configurations to handle complex nested structures while maintaining proper variable interpolation.
