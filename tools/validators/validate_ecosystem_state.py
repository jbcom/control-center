#!/usr/bin/env python3
"""Validator for ECOSYSTEM_STATE.json.

This script validates:
- JSON syntax
- Required fields
- Data consistency
- Repository references
"""

import json
import sys
from pathlib import Path


def validate_json_syntax() -> list[str]:
    """Validate JSON syntax."""
    errors = []
    state_file = Path("ecosystem/ECOSYSTEM_STATE.json")

    if not state_file.exists():
        return ["❌ ecosystem/ECOSYSTEM_STATE.json not found"]

    try:
        with open(state_file) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"❌ Invalid JSON syntax: {e}")

    return errors


def validate_structure() -> list[str]:
    """Validate the structure of ECOSYSTEM_STATE.json."""
    errors = []
    state_file = Path("ecosystem/ECOSYSTEM_STATE.json")

    try:
        with open(state_file) as f:
            state = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []  # Caught elsewhere

    # Check for required top-level keys (support both v1 and v2 schemas)
    # v1 schema: repositories, standards, last_updated
    # v2 schema: active_repositories, management_hub, last_updated
    has_v1_repos = "repositories" in state
    has_v2_repos = "active_repositories" in state
    
    if not has_v1_repos and not has_v2_repos:
        errors.append("❌ Missing required field: 'repositories' or 'active_repositories'")
    
    if "last_updated" not in state:
        errors.append("❌ Missing required field: 'last_updated'")

    # Get repositories from either v1 or v2 schema
    repos_key = "active_repositories" if has_v2_repos else "repositories"
    repos = state.get(repos_key, [])
    
    # Validate repositories structure (repositories can be either a list or a dict)
    if isinstance(repos, list):
        if not repos:
            errors.append(f"⚠️  '{repos_key}' list is empty")
        else:
            for idx, repo_data in enumerate(repos):
                if not isinstance(repo_data, dict):
                    errors.append(f"❌ Repository at index {idx} must be an object")
                    continue

                # Check for required repo fields (v2 has simpler requirements)
                required_repo_fields = ["name", "status"]
                for field in required_repo_fields:
                    if field not in repo_data:
                        repo_name = repo_data.get("name", f"index {idx}")
                        errors.append(
                            f"⚠️  Repository '{repo_name}' missing field: '{field}'"
                        )
    elif isinstance(repos, dict):
        if not repos:
            errors.append(f"⚠️  '{repos_key}' dict is empty")
        else:
            for repo_name, repo_data in repos.items():
                if not isinstance(repo_data, dict):
                    errors.append(f"❌ Repository '{repo_name}' must be an object")
                    continue

                # Check for required repo fields
                required_repo_fields = ["status"]
                for field in required_repo_fields:
                    if field not in repo_data:
                        errors.append(
                            f"⚠️  Repository '{repo_name}' missing field: '{field}'"
                        )
    else:
        errors.append(f"❌ '{repos_key}' must be a list or object")

    # Validate standards structure (only required for v1 schema)
    if has_v1_repos and "standards" in state:
        if not isinstance(state["standards"], dict):
            errors.append("❌ 'standards' must be an object")

    return errors


def validate_repository_consistency() -> list[str]:
    """Validate consistency between repositories and other files."""
    errors = []
    state_file = Path("ecosystem/ECOSYSTEM_STATE.json")

    try:
        with open(state_file) as f:
            state = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

    # Support both v1 (repositories) and v2 (active_repositories) schemas
    repos_key = "active_repositories" if "active_repositories" in state else "repositories"
    if repos_key not in state:
        return []

    repos = state[repos_key]
    
    # Handle both list and dict formats
    repo_names: list[str] = []
    if isinstance(repos, list):
        repo_names = [r.get("name", "") for r in repos if isinstance(r, dict)]
    elif isinstance(repos, dict):
        repo_names = list(repos.keys())

    # Check that documented repos in ecosystem.md match
    ecosystem_md = Path(".ruler/ecosystem.md")
    if ecosystem_md.exists():
        ecosystem_content = ecosystem_md.read_text()

        for repo_name in repo_names:
            if repo_name and repo_name not in ecosystem_content:
                errors.append(
                    f"⚠️  Repository '{repo_name}' not documented in ecosystem.md"
                )

    return errors


def main() -> None:
    """Run all ecosystem state validation checks."""
    print("🔍 Validating ECOSYSTEM_STATE.json...")

    all_errors: list[str] = []

    # Run validators
    validators = [
        ("JSON Syntax", validate_json_syntax),
        ("Structure", validate_structure),
        ("Repository Consistency", validate_repository_consistency),
    ]

    for name, validator in validators:
        print(f"\n  Checking {name}...")
        errors = validator()
        if errors:
            all_errors.extend(errors)
            for error in errors:
                print(f"    {error}")
        else:
            print(f"    ✅ {name} valid")

    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ Validation failed with {len(all_errors)} error(s)/warning(s)")
        # Only fail on actual errors, not warnings
        has_errors = any("❌" in error for error in all_errors)
        sys.exit(1 if has_errors else 0)
    else:
        print("✅ ECOSYSTEM_STATE.json is valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
