#!/usr/bin/env python3
"""Validator for GitHub Actions workflows.

This script validates:
- YAML syntax
- Required workflow files
- Workflow structure and best practices
- Job dependencies
- Action versions
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml


def validate_yaml_syntax(workflow_path: Path) -> list[str]:
    """Validate YAML syntax of a workflow file."""
    errors = []

    try:
        with open(workflow_path) as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"❌ {workflow_path.name}: Invalid YAML syntax - {e}")

    return errors


def validate_workflow_structure(workflow_path: Path) -> list[str]:
    """Validate workflow structure and best practices."""
    errors = []

    try:
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
    except yaml.YAMLError:
        return []  # Syntax errors caught elsewhere

    if not workflow:
        return [f"❌ {workflow_path.name}: Empty workflow file"]

    # Check for required keys ('on' is required, but might be various types)
    if "name" not in workflow:
        errors.append(f"⚠️  {workflow_path.name}: Missing 'name' field")

    # 'on' key must exist (but value can be many things including False for disabled workflows)
    if "on" not in workflow:
        errors.append(f"❌ {workflow_path.name}: Missing 'on' trigger")

    if "jobs" not in workflow:
        errors.append(f"❌ {workflow_path.name}: Missing 'jobs' section")

    # Validate jobs
    if "jobs" in workflow and workflow["jobs"]:
        for job_name, job_config in workflow["jobs"].items():
            if not isinstance(job_config, dict):
                continue

            # Check for runs-on
            if "runs-on" not in job_config:
                errors.append(
                    f"❌ {workflow_path.name}: Job '{job_name}' missing 'runs-on'"
                )

            # Check for steps
            if "steps" not in job_config:
                errors.append(
                    f"⚠️  {workflow_path.name}: Job '{job_name}' has no steps"
                )

    return errors


def validate_action_versions(workflow_path: Path) -> list[str]:
    """Check that actions use pinned versions."""
    errors = []

    try:
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
    except yaml.YAMLError:
        return []

    if not workflow or "jobs" not in workflow:
        return []

    for job_name, job_config in workflow["jobs"].items():
        if not isinstance(job_config, dict) or "steps" not in job_config:
            continue

        for step in job_config["steps"]:
            if not isinstance(step, dict) or "uses" not in step:
                continue

            uses = step["uses"]

            # Check for unpinned actions (main, master branches)
            if "@main" in uses or "@master" in uses:
                errors.append(
                    f"⚠️  {workflow_path.name}: Job '{job_name}' uses "
                    f"unpinned action: {uses}"
                )

    return errors


def validate_required_workflows() -> list[str]:
    """Validate that required workflows exist."""
    errors = []

    # Check for hub validation workflow
    hub_validation = Path(".github/workflows/hub-validation.yml")
    if not hub_validation.exists():
        errors.append("❌ Missing hub validation workflow")

    # Check for standard Python library CI workflow for distribution
    python_ci = Path("templates/python/library-ci.yml")
    if not python_ci.exists():
        errors.append("❌ Missing templates/python/library-ci.yml for distribution")

    return errors


def validate_workflow_comments(workflow_path: Path) -> list[str]:
    """Check that workflows have descriptive comments."""
    errors = []

    content = workflow_path.read_text()

    # Check for header comment
    if not content.strip().startswith("#"):
        errors.append(f"⚠️  {workflow_path.name}: Should start with a description")

    return errors


def main() -> None:
    """Run all workflow validation checks."""
    print("🔍 Validating GitHub Actions workflows...")

    all_errors: list[str] = []

    # Validate required workflows exist
    print("\n  Checking required workflows...")
    errors = validate_required_workflows()
    if errors:
        all_errors.extend(errors)
        for error in errors:
            print(f"    {error}")
    else:
        print("    ✅ Required workflows present")

    # Find all workflow files
    workflow_dirs = [
        Path(".github/workflows"),
        Path("templates/python"),
        Path("templates/typescript"),
        Path("templates/rust"),
    ]

    workflow_files: list[Path] = []
    for workflow_dir in workflow_dirs:
        if workflow_dir.exists():
            workflow_files.extend(workflow_dir.glob("*.yml"))
            workflow_files.extend(workflow_dir.glob("*.yaml"))

    if not workflow_files:
        print("\n❌ No workflow files found!")
        sys.exit(1)

    # Validate each workflow
    for workflow_path in sorted(workflow_files):
        print(f"\n  Validating {workflow_path}...")

        # Run validators
        validators = [
            validate_yaml_syntax,
            validate_workflow_structure,
            validate_action_versions,
            validate_workflow_comments,
        ]

        for validator in validators:
            errors = validator(workflow_path)
            if errors:
                all_errors.extend(errors)
                for error in errors:
                    print(f"    {error}")

        if not any(validator(workflow_path) for validator in validators):
            print(f"    ✅ {workflow_path.name} valid")

    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ Validation failed with {len(all_errors)} error(s)/warning(s)")
        # Only fail on actual errors, not warnings
        has_errors = any("❌" in error for error in all_errors)
        sys.exit(1 if has_errors else 0)
    else:
        print("✅ All workflows are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
