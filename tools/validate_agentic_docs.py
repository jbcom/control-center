#!/usr/bin/env python3
"""Validator for agentic documentation structure and content.

This script validates:
- Ruler directory structure
- AGENTS.md content completeness
- Copilot agent definitions
- Cross-references between docs
"""

import json
import re
import sys
from pathlib import Path


def validate_ruler_structure() -> list[str]:
    """Validate the .ruler directory structure."""
    errors = []
    ruler_dir = Path(".ruler")

    if not ruler_dir.exists():
        errors.append("❌ .ruler directory does not exist")
        return errors

    required_files = {
        "AGENTS.md": "Core agent guidelines",
        "ruler.toml": "Ruler configuration",
        "ecosystem.md": "Ecosystem documentation",
        "cursor.md": "Cursor-specific instructions",
        "copilot.md": "Copilot quick reference",
    }

    for file, description in required_files.items():
        file_path = ruler_dir / file
        if not file_path.exists():
            errors.append(f"❌ Missing {file} - {description}")
        elif file_path.stat().st_size == 0:
            errors.append(f"❌ {file} is empty")

    return errors


def validate_agents_md() -> list[str]:
    """Validate AGENTS.md content."""
    errors = []
    agents_md = Path(".ruler/AGENTS.md")

    if not agents_md.exists():
        return ["❌ .ruler/AGENTS.md not found"]

    content = agents_md.read_text()

    # Check for required sections
    required_sections = [
        "CalVer",
        "Calendar Versioning",
        "semantic-release",
        "Auto-increment",
        "GitHub",
    ]

    for section in required_sections:
        if section.lower() not in content.lower():
            errors.append(f"❌ AGENTS.md missing mention of '{section}'")

    # Check for misconceptions section
    if "misconception" not in content.lower():
        errors.append("❌ AGENTS.md should document common misconceptions")

    # Check for proper formatting
    if not re.search(r"^#+\s+", content, re.MULTILINE):
        errors.append("❌ AGENTS.md should use markdown headers")

    return errors


def validate_copilot_agents() -> list[str]:
    """Validate Copilot agent definitions."""
    errors = []
    copilot_dir = Path(".copilot/agents")

    if not copilot_dir.exists():
        errors.append("⚠️  .copilot/agents directory not found")
        return errors

    agent_files = list(copilot_dir.glob("*.agent.md"))
    if not agent_files:
        errors.append("⚠️  No Copilot agents defined")
        return errors

    for agent_file in agent_files:
        content = agent_file.read_text()

        # Check for required agent sections
        if "# " not in content:
            errors.append(f"❌ {agent_file.name} missing title")

        if "## Commands" not in content and "commands" not in content.lower():
            errors.append(f"⚠️  {agent_file.name} should define commands")

    return errors


def validate_ecosystem_docs() -> list[str]:
    """Validate ecosystem documentation consistency."""
    errors = []

    # Check ecosystem.md exists
    ecosystem_md = Path(".ruler/ecosystem.md")
    if not ecosystem_md.exists():
        errors.append("❌ .ruler/ecosystem.md not found")
        return errors

    # Check ECOSYSTEM_STATE.json exists
    state_json = Path("ECOSYSTEM_STATE.json")
    if not state_json.exists():
        errors.append("❌ ECOSYSTEM_STATE.json not found")
        return errors

    # Validate they reference the same repos
    ecosystem_content = ecosystem_md.read_text()
    state_data = json.loads(state_json.read_text())

    repos = state_data.get("repositories", [])
    if isinstance(repos, list):
        # If repositories is a list of objects
        for repo in repos:
            if isinstance(repo, dict):
                repo_name = repo.get("name", "")
                if repo_name and repo_name not in ecosystem_content:
                    errors.append(
                        f"⚠️  Repository '{repo_name}' in ECOSYSTEM_STATE.json "
                        f"but not documented in ecosystem.md"
                    )
    elif isinstance(repos, dict):
        # If repositories is a dict
        for repo_name in repos.keys():
            if repo_name not in ecosystem_content:
                errors.append(
                    f"⚠️  Repository '{repo_name}' in ECOSYSTEM_STATE.json "
                    f"but not documented in ecosystem.md"
                )

    return errors


def validate_cross_references() -> list[str]:
    """Validate cross-references between documentation files."""
    errors = []
    ruler_dir = Path(".ruler")

    if not ruler_dir.exists():
        return errors

    # Check that generated files exist
    root_agents = Path("AGENTS.md")
    if not root_agents.exists():
        errors.append("⚠️  AGENTS.md (generated) not found - run 'ruler apply'")

    root_cursorrules = Path(".cursorrules")
    if not root_cursorrules.exists():
        errors.append("⚠️  .cursorrules (generated) not found - run 'ruler apply'")

    return errors


def main() -> None:
    """Run all validation checks."""
    print("🔍 Validating agentic documentation...")

    all_errors: list[str] = []

    # Run all validators
    validators = [
        ("Ruler Structure", validate_ruler_structure),
        ("AGENTS.md Content", validate_agents_md),
        ("Copilot Agents", validate_copilot_agents),
        ("Ecosystem Documentation", validate_ecosystem_docs),
        ("Cross-References", validate_cross_references),
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
        print(f"❌ Validation failed with {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print("✅ All agentic documentation is valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
