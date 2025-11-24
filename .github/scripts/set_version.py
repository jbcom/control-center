#!/usr/bin/env python3
# ruff: noqa: T201, D103, EM101, PTH123
"""Auto-version script: Updates version based on GitHub run number.

Uses CalVer format: YYYY.MM.BUILD_NUMBER
Example: 2025.11.42

This ensures:
- Every push to main gets a unique, incrementing version
- No manual version management needed
- No git tags required
- Always publishable to PyPI
"""
import os
import re
import sys

from datetime import datetime, timezone
from pathlib import Path


def find_init_file():
    """Find the __init__.py file with a valid __version__ declaration."""
    src = Path("src")
    if not src.exists():
        raise FileNotFoundError("src/ directory not found")

    found_files = [
        f for f in src.rglob("__init__.py") if "__version__" in f.read_text()
    ]

    if not found_files:
        raise FileNotFoundError("No __init__.py with __version__ found in src/")
    if len(found_files) > 1:
        msg = f"Multiple __init__.py files with __version__ found: {found_files}"
        raise FileNotFoundError(msg)
    return found_files[0]


def update_docs_version(new_version: str) -> None:
    """Update version in docs/conf.py."""
    docs_conf = Path("docs/conf.py")
    if not docs_conf.exists():
        # Docs config is optional - don't fail if it doesn't exist
        print("docs/conf.py not found, skipping docs version update")
        return

    content = docs_conf.read_text()
    lines = content.splitlines(keepends=True)

    # Match: version = "x.y.z" with optional spaces
    version_pattern = re.compile(r'^(\s*)version\s*=\s*(["\']).*?\2')

    updated = False
    for i, line in enumerate(lines):
        match = version_pattern.match(line)
        if match:
            indent = match.group(1)
            remainder = line[match.end() :]
            lines[i] = f'{indent}version = "{new_version}"{remainder}'
            updated = True
            break

    if updated:
        docs_conf.write_text("".join(lines))
        print(f"Updated version in {docs_conf}")
    else:
        print(f"Warning: Could not find version assignment in {docs_conf}")


def main():
    # Get GitHub run number (always incrementing)
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "0")

    # Get current date in UTC
    now = datetime.now(timezone.utc)

    # Generate CalVer: YYYY.MM.BUILD (month not zero-padded; project-specific choice for brevity, not required by CalVer)
    new_version = f"{now.year}.{now.month}.{run_number}"

    # Find and update __init__.py
    init_file = find_init_file()
    content = init_file.read_text()

    lines = content.splitlines(keepends=True)
    # Regex to match exactly "__version__" assignment, not __version_info__ or similar
    # Matches: __version__ = "..." or __version__="..." (with/without spaces)
    version_pattern = re.compile(r'^(\s*)__version__\s*=\s*(["\']).*?\2')

    updated = False
    for i, line in enumerate(lines):
        match = version_pattern.match(line)
        if match:
            # Preserve original indentation
            indent = match.group(1)
            # Preserve everything after the closing quote (including newline)
            remainder = line[match.end() :]
            lines[i] = f'{indent}__version__ = "{new_version}"{remainder}'
            updated = True
            break

    if not updated:
        msg = f"Failed to update __version__ in {init_file}"
        raise ValueError(msg)

    init_file.write_text("".join(lines))
    print(f"Generated version: {new_version}")
    print(f"Updated version in {init_file}")

    # Update docs/conf.py version
    update_docs_version(new_version)

    # Set output for workflow
    if github_output := os.environ.get("GITHUB_OUTPUT"):
        with open(github_output, "a") as f:
            f.write(f"version={new_version}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
