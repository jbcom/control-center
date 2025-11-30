"""Terraform external data provider runtime.

This module provides the runtime that receives requests from Terraform
via stdin/environment and returns results via stdout.

The runtime can be invoked either by:
1. Running `python -m python_terraform_bridge <method_name>`
2. Using the `terraform-bridge` CLI
3. Programmatically via TerraformRuntime.invoke()
"""

from __future__ import annotations

import base64
import json
import secrets
import sys
from typing import TYPE_CHECKING, Any

from directed_inputs_class import DirectedInputsClass
from extended_data_types import get_available_methods
from lifecyclelogging import Logging

if TYPE_CHECKING:
    from collections.abc import Callable


class TerraformRuntime:
    """Runtime for executing Terraform data source methods.

    This class handles:
    1. Reading input from Terraform (stdin JSON or environment variables)
    2. Invoking the appropriate method
    3. Returning results in Terraform-compatible format (JSON with base64 encoding)

    Example:
        class MyDataSource(DirectedInputsClass):
            def list_users(self, domain: str = None) -> dict:
                return {"user1": {...}}

        runtime = TerraformRuntime(MyDataSource)
        runtime.run()  # Handle stdin/stdout
    """

    def __init__(
        self,
        data_source_class: type[Any],
        null_resource_class: type[Any] | None = None,
        logging: Logging | None = None,
    ) -> None:
        """Initialize the runtime.

        Args:
            data_source_class: Class containing data source methods.
            null_resource_class: Optional class for null resource methods.
            logging: Optional logging configuration.
        """
        self.data_source_class = data_source_class
        self.null_resource_class = null_resource_class
        self.logging = logging or Logging(
            enable_console=False,
            enable_file=True,
            logger_name="terraform_bridge",
        )
        self.logger = self.logging.logger

        # Build method registry
        self._data_source_methods = get_available_methods(data_source_class)
        self._null_resource_methods = (
            get_available_methods(null_resource_class) if null_resource_class else {}
        )

    def get_available_methods(self) -> dict[str, str]:
        """Get all available method names and descriptions.

        Returns:
            Dict mapping method names to docstrings.
        """
        methods = {}
        methods.update(self._data_source_methods)
        methods.update(self._null_resource_methods)
        return methods

    def invoke(
        self,
        method_name: str,
        from_stdin: bool = True,
        to_stdout: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Invoke a method by name.

        Args:
            method_name: Name of the method to invoke.
            from_stdin: Read additional args from stdin.
            to_stdout: Write result to stdout.
            **kwargs: Method arguments.

        Returns:
            Method result.
        """
        if method_name in self._data_source_methods:
            instance = self._instantiate_target(
                self.data_source_class,
                from_stdin=from_stdin,
                to_stdout=to_stdout,
                resource_type="data_source",
            )
        elif method_name in self._null_resource_methods and self.null_resource_class:
            instance = self._instantiate_target(
                self.null_resource_class,
                from_stdin=from_stdin,
                to_stdout=to_stdout,
                resource_type="null_resource",
            )
        else:
            available = list(self._data_source_methods.keys()) + list(
                self._null_resource_methods.keys()
            )
            raise ValueError(f"Unknown method: {method_name}. Available: {available}")

        method = getattr(instance, method_name, None)
        if method is None:
            raise AttributeError(f"Method {method_name} not found on {instance}")

        # Invoke the method
        result = method(**kwargs)

        if to_stdout:
            self._output_result(result, method_name)

        return result

    def _output_result(self, result: Any, method_name: str) -> None:
        """Format and output result to stdout for Terraform.

        Terraform external data requires string values, so we base64 encode
        complex data structures.

        Args:
            result: Method result to output.
            method_name: Name of the method (used as output key).
        """
        if isinstance(result, dict) and all(isinstance(v, str) for v in result.values()):
            # Already a string dict, output directly
            output = result
        else:
            # Encode as base64 JSON
            encoded = base64.b64encode(json.dumps(result, default=str).encode()).decode()
            output = {method_name: encoded}

        print(json.dumps(output))

    def run(self, args: list[str] | None = None) -> None:
        """Run the runtime as a CLI.

        Args:
            args: Command line arguments (defaults to sys.argv).
        """
        if args is None:
            args = sys.argv[1:]

        if not args:
            self._print_help()
            sys.exit(1)

        method_name = "_".join(args)

        if method_name == "show_methods":
            methods = {
                "data_sources": list(self._data_source_methods.keys()),
                "resources": list(self._null_resource_methods.keys()),
            }
            print(json.dumps(methods, indent=2))
            sys.exit(0)

        if method_name not in self.get_available_methods():
            self.logger.error(f"Unknown method: {method_name}")
            self._print_help()
            sys.exit(1)

        try:
            self.invoke(method_name, from_stdin=True, to_stdout=True)
        except Exception as e:
            error_id = self._handle_exception(method_name, e)
            print(json.dumps(self._format_public_error(error_id)))
            sys.exit(1)

    def _print_help(self) -> None:
        """Print help message."""
        help_txt = "Terraform Bridge Runtime\n\n"
        help_txt += "Usage: python -m python_terraform_bridge <method_name>\n\n"

        help_txt += "Data Sources:\n"
        for name, docs in self._data_source_methods.items():
            if name.startswith("_") or (docs and "NOPARSE" in docs):
                continue
            desc = docs.splitlines()[0] if docs else ""
            help_txt += f"  {name}: {desc}\n"

        if self._null_resource_methods:
            help_txt += "\nNull Resources:\n"
            for name, docs in self._null_resource_methods.items():
                if name.startswith("_"):
                    continue
                desc = docs.splitlines()[0] if docs else ""
                help_txt += f"  {name}: {desc}\n"

        print(help_txt)

    def _instantiate_target(
        self,
        target_class: type[Any],
        *,
        from_stdin: bool,
        to_stdout: bool,
        resource_type: str,
    ) -> Any:
        """Instantiate either a legacy DirectedInputsClass or decorator-based class."""

        if issubclass(target_class, DirectedInputsClass):
            return target_class(
                to_console=not to_stdout,
                to_file=True,
                from_stdin=from_stdin,
                logging=self.logging,
            )

        if getattr(target_class, "__directed_inputs_enabled__", False):
            return target_class(
                _directed_inputs_config={"from_stdin": from_stdin},
                _directed_inputs_runtime_logging=self.logging,
                _directed_inputs_runtime_settings={
                    "to_console": not to_stdout,
                    "to_file": True,
                    "resource_type": resource_type,
                },
            )

        raise TypeError(
            f"{target_class.__name__} must inherit from DirectedInputsClass "
            "or be decorated with @directed_inputs"
        )

    def _handle_exception(self, method_name: str, error: Exception) -> str:
        """Log exceptions and return a public-safe error reference."""

        error_id = secrets.token_hex(8)
        self.logger.error(
            "Method %s failed (error_id=%s): %s",
            method_name,
            error_id,
            error,
            exc_info=True,
        )
        return error_id

    @staticmethod
    def _format_public_error(error_id: str) -> dict[str, str]:
        """Return sanitized error payload suitable for Terraform consumers."""

        return {
            "error": "Terraform bridge execution failed. "
            "Refer to logs with the provided reference.",
            "reference": error_id,
        }


def invoke_method_with_kwargs(
    data_source_class: type[Any],
    method_name: str,
    null_resource_class: type[Any] | None = None,
    **kwargs: Any,
) -> Any:
    """Invoke a method with explicit kwargs (for Lambda/programmatic use).

    Args:
        data_source_class: Class containing data source methods.
        method_name: Name of the method to invoke.
        null_resource_class: Optional class for null resources.
        **kwargs: Method arguments.

    Returns:
        Method result.
    """
    runtime = TerraformRuntime(
        data_source_class=data_source_class,
        null_resource_class=null_resource_class,
    )

    return runtime.invoke(
        method_name,
        from_stdin=False,
        to_stdout=False,
        **kwargs,
    )


def lambda_handler_factory(
    data_source_class: type[Any],
    null_resource_class: type[Any] | None = None,
) -> Callable[[dict[str, Any], Any], dict[str, Any]]:
    """Create an AWS Lambda handler for Terraform bridge methods.

    Args:
        data_source_class: Class containing data source methods.
        null_resource_class: Optional class for null resources.

    Returns:
        Lambda handler function.

    Example:
        from my_service import MyDataSource

        handler = lambda_handler_factory(MyDataSource)

        # In Lambda:
        # {
        #   "method": "list_users",
        #   "kwargs": {"domain": "example.com"}
        # }
    """
    runtime = TerraformRuntime(
        data_source_class=data_source_class,
        null_resource_class=null_resource_class,
    )

    def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
        logging = Logging(
            enable_console=True,
            enable_file=False,
            logger_name="lambda_handler",
        )
        logger = logging.logger

        logger.info("Lambda invoked", extra={"keys": sorted(event.keys())})

        try:
            method_name = event.get("method")
            if not method_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {
                            "error": "No method specified",
                            "available": list(runtime.get_available_methods().keys()),
                        }
                    ),
                }

            kwargs = event.get("kwargs", {})
            logger.info("Invoking %s with %d kwargs keys", method_name, len(kwargs))

            result = runtime.invoke(
                method_name,
                from_stdin=False,
                to_stdout=False,
                **kwargs,
            )

            return {
                "statusCode": 200,
                "body": json.dumps(result, default=str) if not isinstance(result, str) else result,
            }

        except Exception as e:
            error_id = runtime._handle_exception(method_name or "unknown", e)
            return {
                "statusCode": 500,
                "body": json.dumps(TerraformRuntime._format_public_error(error_id)),
            }

    return handler
