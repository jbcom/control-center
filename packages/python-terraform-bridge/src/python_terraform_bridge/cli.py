"""Command-line interface for python-terraform-bridge.

This module provides the `terraform-bridge` CLI command.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def generate_command(args: argparse.Namespace) -> int:
    """Handle the 'generate' subcommand.

    Generates Terraform modules from a Python class.
    """
    from extended_data_types import get_available_methods

    from python_terraform_bridge.module_resources import TerraformModuleResources

    # Import the target class
    module_path, class_name = args.target.rsplit(":", 1)
    try:
        import importlib

        module = importlib.import_module(module_path)
        target_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing {args.target}: {e}", file=sys.stderr)
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    methods = get_available_methods(target_class)

    generated = 0
    for method_name, docstring in methods.items():
        if method_name.startswith("_"):
            continue
        if docstring and "NOPARSE" in docstring:
            continue

        resources = TerraformModuleResources(
            module_name=method_name,
            docstring=docstring,
            terraform_modules_dir=str(output_dir),
            terraform_modules_class=args.module_class,
            binary_name=args.binary or "python -m python_terraform_bridge",
        )

        if resources.generation_forbidden:
            continue

        module_path = resources.get_module_path()
        module_json = resources.get_mixed()

        module_path.parent.mkdir(parents=True, exist_ok=True)

        with module_path.open("w") as f:
            json.dump(module_json, f, indent=2)

        print(f"Generated: {module_path}")
        generated += 1

    print(f"\nGenerated {generated} Terraform modules in {output_dir}")
    return 0


def list_command(args: argparse.Namespace) -> int:
    """Handle the 'list' subcommand.

    Lists available methods from a Python class.
    """
    from extended_data_types import get_available_methods

    # Import the target class
    module_path, class_name = args.target.rsplit(":", 1)
    try:
        import importlib

        module = importlib.import_module(module_path)
        target_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing {args.target}: {e}", file=sys.stderr)
        return 1

    methods = get_available_methods(target_class)

    if args.json:
        output: dict[str, Any] = {}
        for name, docs in methods.items():
            if name.startswith("_"):
                continue
            if docs and "NOPARSE" in docs:
                continue
            output[name] = docs.splitlines()[0] if docs else ""
        print(json.dumps(output, indent=2))
    else:
        print(f"Methods in {args.target}:\n")
        for name, docs in methods.items():
            if name.startswith("_"):
                continue
            if docs and "NOPARSE" in docs:
                continue
            desc = docs.splitlines()[0] if docs else ""
            print(f"  {name}: {desc}")

    return 0


def run_command(args: argparse.Namespace) -> int:
    """Handle the 'run' subcommand.

    Runs as a Terraform external data provider.
    """
    # This is for direct invocation - handled by __main__.py
    # This subcommand provides an explicit way to run
    import importlib

    from python_terraform_bridge.runtime import TerraformRuntime

    # Import the target class
    module_path, class_name = args.target.rsplit(":", 1)
    try:
        module = importlib.import_module(module_path)
        target_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing {args.target}: {e}", file=sys.stderr)
        return 1

    runtime = TerraformRuntime(data_source_class=target_class)

    # Get remaining args as method name
    method_args = args.method_args or []
    runtime.run(method_args)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="terraform-bridge",
        description="Bridge Python classes to Terraform external data sources",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 202511.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate Terraform modules from a Python class",
    )
    gen_parser.add_argument(
        "target",
        help="Python class to generate from (e.g., mymodule:MyClass)",
    )
    gen_parser.add_argument(
        "-o",
        "--output",
        default="terraform-modules",
        help="Output directory for generated modules",
    )
    gen_parser.add_argument(
        "-c",
        "--module-class",
        default="",
        help="Module class prefix",
    )
    gen_parser.add_argument(
        "-b",
        "--binary",
        default=None,
        help="Binary command for runtime invocation",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available methods from a Python class",
    )
    list_parser.add_argument(
        "target",
        help="Python class to inspect (e.g., mymodule:MyClass)",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run as Terraform external data provider",
    )
    run_parser.add_argument(
        "target",
        help="Python class to run (e.g., mymodule:MyClass)",
    )
    run_parser.add_argument(
        "method_args",
        nargs="*",
        help="Method name (parts separated by spaces become underscores)",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "generate":
        return generate_command(args)
    elif args.command == "list":
        return list_command(args)
    elif args.command == "run":
        return run_command(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
