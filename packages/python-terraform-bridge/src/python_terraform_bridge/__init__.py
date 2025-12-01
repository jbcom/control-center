"""Python Terraform Bridge - Bridge Python classes to Terraform external data sources.

This package provides tools to:
1. Generate Terraform modules from DirectedInputsClass methods
2. Run as an external data provider for Terraform
3. Support both docstring-based and decorator-based registration

Example usage with decorators:

    from python_terraform_bridge import TerraformRegistry, data_source
    from directed_inputs_class import DirectedInputsClass

    registry = TerraformRegistry()

    class MyConnector(DirectedInputsClass):
        @registry.data_source(key="users", module_class="myservice")
        def list_users(self, domain: str = None) -> dict:
            '''List all users.'''
            return {"user1": {...}, "user2": {...}}

    # Generate Terraform modules
    registry.generate_modules("./terraform-modules")

    # Or run as external data provider
    if __name__ == "__main__":
        registry.run()

Example usage with docstrings (legacy/compatible):

    class MyDataSource(DirectedInputsClass):
        def list_users(self, domain: str = None) -> dict:
            '''List all users.

            generator=key: users, module_class: myservice

            name: domain, required: false, type: string
            '''
            return {"user1": {...}, "user2": {...}}

    # Parse and generate
    from python_terraform_bridge import TerraformModuleResources
    resources = TerraformModuleResources(
        module_name="list_users",
        docstring=MyDataSource.list_users.__doc__,
    )
"""

from python_terraform_bridge.module_resources import TerraformModuleResources
from python_terraform_bridge.parameter import TerraformModuleParameter
from python_terraform_bridge.registry import TerraformRegistry, data_source, null_resource
from python_terraform_bridge.runtime import TerraformRuntime

__all__ = [
    "TerraformModuleParameter",
    "TerraformModuleResources",
    "TerraformRegistry",
    "TerraformRuntime",
    "data_source",
    "null_resource",
]

__version__ = "1.2.0"
