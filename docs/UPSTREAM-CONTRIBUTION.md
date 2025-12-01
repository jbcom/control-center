# Upstream Contribution Guide: FSC → jbcom

## Overview

This guide documents how FSC Control Center agents contribute features, fixes, and improvements upstream to the jbcom ecosystem packages.

## When to Contribute Upstream

### ✅ Do Contribute When

- FSC needs a feature that would benefit the package generally
- FSC found a bug in a jbcom package
- FSC has an optimization that improves performance
- FSC has better error handling or edge case coverage
- Feature would be useful to other jbcom package consumers

### ❌ Don't Contribute When

- Change is FSC-specific and wouldn't help other users
- Feature is experimental and not production-ready
- Change would break backward compatibility without good reason
- Similar feature already exists (check first!)

## Pre-Contribution Checklist

Before starting:

```bash
# 1. Check if feature already exists
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list --repo jbcom/jbcom-control-center --search "<feature>"
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr list --repo jbcom/jbcom-control-center --search "<feature>"

# 2. Check jbcom wiki for existing patterns
# https://github.com/jbcom/jbcom-control-center/wiki

# 3. Review jbcom coding standards
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api /repos/jbcom/jbcom-control-center/contents/wiki/Python-Standards.md --jq '.content' | base64 -d
```

## Contribution Workflow

### Step 1: Clone jbcom Control Center

```bash
cd /tmp
GH_TOKEN="$GITHUB_JBCOM_TOKEN" git clone https://$GITHUB_JBCOM_TOKEN@github.com/jbcom/jbcom-control-center.git
cd jbcom-control-center
```

### Step 2: Understand the Structure

```
jbcom-control-center/
├── packages/
│   ├── extended-data-types/      # Foundation utilities
│   │   ├── src/extended_data_types/
│   │   │   ├── __init__.py
│   │   │   └── *.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── lifecyclelogging/         # Logging framework
│   ├── directed-inputs-class/    # Input validation
│   └── vendor-connectors/        # Cloud integrations
├── pyproject.toml                # Workspace root
├── packages/ECOSYSTEM.toml       # Package metadata
└── .github/workflows/ci.yml      # CI/CD
```

### Step 3: Create Feature Branch

```bash
# Branch naming: feat/fsc-<descriptive-name>
git checkout -b feat/fsc-<feature-name>

# For bug fixes
git checkout -b fix/fsc-<bug-description>
```

### Step 4: Make Changes

#### Locate the Right Package

| If you need... | Edit package... |
|----------------|-----------------|
| Type conversions, serialization | extended-data-types |
| Logging, sanitization | lifecyclelogging |
| Input validation | directed-inputs-class |
| Cloud integrations (AWS, GCP, etc) | vendor-connectors |

#### Follow jbcom Conventions

**File Structure:**
```python
# src/package_name/module.py

"""Module docstring explaining purpose."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Public API
__all__ = ["function_name", "ClassName"]


def function_name(arg: str) -> str:
    """Function docstring.
    
    Args:
        arg: Description of argument.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: When arg is invalid.
    """
    return arg
```

**Add Tests:**
```python
# tests/test_module.py

import pytest
from package_name.module import function_name


def test_function_basic():
    """Test basic functionality."""
    result = function_name("input")
    assert result == "expected"


def test_function_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        function_name("")
```

### Step 5: Run Quality Checks

```bash
# Navigate to package
cd packages/extended-data-types  # or whichever package

# Run tests
pytest

# Run linting
ruff check --fix src/ tests/
ruff format src/ tests/

# Run type checking
mypy src/

# Run all checks
cd ../..  # back to root
make check  # if Makefile exists
```

### Step 6: Commit with Conventional Format

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
| Type | Purpose | Version Bump |
|------|---------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `perf` | Performance improvement | Patch |
| `refactor` | Code refactoring | None |
| `docs` | Documentation | None |
| `test` | Tests | None |
| `chore` | Maintenance | None |

**Scopes:**
| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

**Examples:**
```bash
# Feature in extended-data-types
git commit -m "feat(edt): add deep merge utility

Adds deep_merge() function for nested dictionary merging.
Needed for FSC terraform-modules config processing.

- Handles nested dicts recursively
- Preserves list contents
- Type-safe implementation"

# Bug fix in lifecyclelogging
git commit -m "fix(logging): handle None values in sanitizer

Previously crashed when log context contained None values.
Now properly handles None by converting to 'null' string.

Fixes jbcom/jbcom-control-center#123"

# Performance improvement
git commit -m "perf(connectors): optimize AWS client caching

Reduces AWS client initialization overhead by 60%.
Implements lazy client creation with thread-safe caching."
```

### Step 7: Push and Create PR

```bash
# Push branch
git push -u origin feat/fsc-<feature-name>

# Create PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --repo jbcom/jbcom-control-center \
  --title "feat(edt): <short description>" \
  --body "## Summary

<1-2 sentence summary of what this PR does>

## Motivation

This feature/fix is needed for  infrastructure:
- <specific use case 1>
- <specific use case 2>

## Changes

- Added \`function_name()\` to extended_data_types
- Added unit tests for new functionality
- Updated docstrings

## Test Plan

- [x] Unit tests added and passing
- [x] Lint passes (ruff check)
- [x] Type check passes (mypy)
- [x] Existing tests still pass

## FSC Integration

After this is released, will be used in:
- /terraform-modules for X
- /fsc-control-center for Y

## Backward Compatibility

✅ No breaking changes

---

*Contributed by FSC Control Center background agent*
*Station-to-station coordination protocol*"
```

### Step 8: Track in FSC

```bash
# Create tracking issue in FSC
gh issue create \
  --repo /fsc-control-center \
  --title "🔗 Upstream PR: jbcom/jbcom-control-center#<PR_NUM>" \
  --label "upstream" \
  --body "## Tracking Upstream Contribution

**PR**: https://github.com/jbcom/jbcom-control-center/pull/<PR_NUM>
**Package**: <package-name>
**Feature**: <description>

## Status Checklist
- [x] PR created
- [ ] PR reviewed by jbcom
- [ ] PR merged
- [ ] Released to PyPI
- [ ] FSC updated to use new version

## FSC Repos That Will Use This
- /terraform-modules
- <other repos>

## Dependencies
<any PRs this depends on or blocks>"

# Update memory bank
cat >> memory-bank/progress.md << 'EOF'

### Upstream Contribution
- Created jbcom PR #<NUM>: <description>
- Tracking in FSC issue #<NUM>
EOF
```

### Step 9: Monitor and Respond

```bash
# Check PR status
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr view <NUM> --repo jbcom/jbcom-control-center

# Check for reviews
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr view <NUM> --repo jbcom/jbcom-control-center --comments

# Respond to feedback
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr comment <NUM> --repo jbcom/jbcom-control-center --body "<response>"
```

### Step 10: After Merge

```bash
# 1. Watch for release
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release list --repo jbcom/<package> --limit 3

# 2. Update FSC dependencies
# When new version is on PyPI, update terraform-modules

# 3. Close tracking issue
gh issue close <FSC_ISSUE_NUM> --comment "Released in jbcom/<package> v<X.Y.Z>"
```

## Responding to jbcom Feedback

### Feedback Types

**Code Quality:**
```markdown
@reviewer Thank you for the feedback. I've addressed:

✅ Improved variable naming per your suggestion
✅ Added docstring for edge cases
✅ Refactored to reduce complexity

Changes in commit <hash>.
```

**Architecture Suggestions:**
```markdown
@reviewer Thank you for the architecture suggestion.

I've considered the alternative approach, but chose the current implementation because:
1. <reason 1>
2. <reason 2>

However, if the jbcom team prefers the alternative, I'm happy to refactor.
```

**Breaking Change Concerns:**
```markdown
@reviewer You're right that this could be a breaking change.

Options:
1. Make it opt-in via parameter (backward compatible)
2. Add deprecation warning, change in next major version
3. Document migration path

I recommend option 1. Would you agree?
```

## Best Practices

### Do

- ✅ Follow jbcom's existing code style exactly
- ✅ Add comprehensive tests
- ✅ Document all public APIs
- ✅ Keep PRs focused and small
- ✅ Respond promptly to feedback
- ✅ Reference FSC use case in PR description

### Don't

- ❌ Mix multiple features in one PR
- ❌ Skip tests "to save time"
- ❌ Ignore jbcom's conventions
- ❌ Create breaking changes without discussion
- ❌ Leave PR unmonitored after creation

## Common Patterns

### Adding a New Utility Function

```python
# 1. Add function to appropriate module
# src/extended_data_types/utils.py

def new_utility(data: dict[str, Any]) -> dict[str, Any]:
    """One-line description.
    
    Longer description if needed.
    
    Args:
        data: Input dictionary to process.
        
    Returns:
        Processed dictionary.
        
    Examples:
        >>> new_utility({"key": "value"})
        {"key": "processed_value"}
    """
    # Implementation
    return processed

# 2. Export in __init__.py
# src/extended_data_types/__init__.py
from .utils import new_utility

__all__ = [..., "new_utility"]

# 3. Add tests
# tests/test_utils.py
def test_new_utility_basic():
    result = new_utility({"key": "value"})
    assert result == {"key": "processed_value"}
```

### Fixing a Bug

```python
# 1. Write failing test first
def test_bug_reproduction():
    """Reproduces bug #123."""
    # This should pass after fix
    result = buggy_function(edge_case_input)
    assert result is not None  # Was raising exception

# 2. Fix the bug
def buggy_function(data):
    if data is None:  # Add missing check
        return default_value
    # rest of implementation

# 3. Verify test passes
# pytest tests/test_module.py::test_bug_reproduction
```

---

**Last Updated**: 2025-11-28  
**Protocol Version**: 1.0
