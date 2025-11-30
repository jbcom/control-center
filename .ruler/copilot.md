# GitHub Copilot Agent Configuration

Comprehensive guide for GitHub Copilot when working in jbcom ecosystem repositories.

## 🚨 CRITICAL: Read First!

### Automatic Issue Handling
When you receive an issue labeled `copilot`:
1. **Read the full issue description** carefully
2. **Check `.ruler/AGENTS.md`** for project rules
3. **Create a feature branch**: `copilot/issue-{number}-{short-description}`
4. **Implement with tests** - every feature needs tests
5. **Run verification**: `ruff check . && pytest`
6. **Create PR** linking to the issue

### Versioning & Releases
✅ Each package uses python-semantic-release (SemVer `MAJOR.MINOR.PATCH`)
✅ Conventional commits with scopes drive version bumps
❌ **NEVER** edit `__version__` or pyproject versions manually
❌ **NEVER** reintroduce alternative versioning schemes, git tag workflows, or manual bump scripts

### Release Process
✅ PSR determines if a release is needed when main is updated
✅ Approved commits trigger: version bump → tag → PyPI publish → repo sync
❌ **NEVER** suggest conditional/manual release steps outside PSR

## Working with Auto-Generated Issues

Issues created by `cursor-fleet analyze` have this structure:
```markdown
## Summary
[Description of the task]

## Priority
`HIGH` or `CRITICAL` or `MEDIUM` or `LOW`

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated if needed
- [ ] CI passes
```

### Your Workflow for These Issues:
1. Parse the Summary for requirements
2. Check Priority - `CRITICAL`/`HIGH` = do first
3. Complete ALL Acceptance Criteria checkboxes
4. Reference the issue number in your PR

## Repository Structure

```
jbcom-control-center/
├── packages/                    # All Python packages (monorepo)
│   ├── extended-data-types/     # Foundation library
│   ├── lifecyclelogging/        # Logging utilities
│   ├── directed-inputs-class/   # Input validation
│   ├── vendor-connectors/       # External service connectors
│   ├── cursor-fleet/            # Agent fleet management (Node.js)
│   └── python-terraform-bridge/ # Terraform utilities
├── .ruler/                      # Agent instructions (source of truth)
├── .github/workflows/           # CI/CD workflows
└── pyproject.toml               # Workspace configuration
```

## Code Patterns

### Python Type Hints (Required)
```python
# ✅ CORRECT - Modern type hints
from collections.abc import Mapping, Sequence
from typing import Any

def process_data(items: list[dict[str, Any]]) -> dict[str, int]:
    """Process items and return counts."""
    return {"count": len(items)}

# ❌ WRONG - Legacy typing
from typing import Dict, List
def process_data(items: Dict[str, Any]) -> List[str]:
    pass
```

### Use Pathlib (Always)
```python
# ✅ CORRECT
from pathlib import Path
config_file = Path("config.yaml")
if config_file.exists():
    content = config_file.read_text()

# ❌ WRONG
import os
config_file = os.path.join("config.yaml")
```

### Error Handling
```python
# ✅ CORRECT - Specific, helpful errors
if not config_file.exists():
    raise FileNotFoundError(
        f"Config file not found: {config_file}. "
        f"Create it with: python setup.py init"
    )

# ❌ WRONG - Vague errors
raise FileNotFoundError("Config not found")
```

## Testing Requirements

### Every Feature Needs Tests
```python
# ✅ CORRECT - Descriptive name, clear assertion
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ✅ CORRECT - Use fixtures for setup
@pytest.fixture
def sample_data():
    return [{"id": i} for i in range(10)]

def test_with_fixture(sample_data):
    result = process_data(sample_data)
    assert result["count"] == 10
```

### Test Edge Cases
- Empty inputs
- Invalid inputs (should raise appropriate errors)
- Boundary conditions
- Large inputs (if performance matters)

## Package Dependencies

### Use extended-data-types Utilities
Before adding any utility function, check if `extended-data-types` provides it:

```python
# ✅ CORRECT - Use existing utilities
from extended_data_types import (
    strtobool,              # String to boolean
    strtopath,              # String to Path
    make_raw_data_export_safe,  # Sanitize data for logging
    get_unique_signature,   # Generate unique IDs
    encode_json,            # JSON serialization
    decode_yaml,            # YAML parsing
)

# ❌ WRONG - Reimplementing existing functionality
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

### Dependency Order (for releases)
1. `extended-data-types` (foundation)
2. `lifecyclelogging` (depends on #1)
3. `directed-inputs-class` (depends on #1)
4. `vendor-connectors` (depends on #1, #2, #3)

## Security Requirements

### Never Log Secrets
```python
# ✅ CORRECT - Sanitize before logging
from extended_data_types import make_raw_data_export_safe
safe_data = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe_data}")

# ❌ WRONG - May log secrets
logger.info(f"Processing: {user_data}")
```

### Validate All Inputs
```python
# ✅ CORRECT - Validate before use
def load_config(filepath: str) -> dict[str, Any]:
    path = Path(filepath)
    if not path.is_file():
        raise ValueError(f"Not a file: {filepath}")
    if path.suffix not in (".json", ".yaml", ".yml"):
        raise ValueError(f"Unsupported format: {path.suffix}")
    return decode_yaml(path.read_text())
```

## Documentation Standards

### Google-Style Docstrings
```python
def process_items(items: list[dict], validate: bool = True) -> dict[str, Any]:
    """Process a list of items and return summary.

    Args:
        items: List of dictionaries containing item data.
        validate: Whether to validate items before processing.

    Returns:
        Dictionary with processing summary and statistics.

    Raises:
        ValueError: If items list is empty or validation fails.

    Example:
        >>> items = [{"id": 1, "name": "Item 1"}]
        >>> process_items(items)
        {"count": 1, "valid": 1}
    """
```

## PR Creation Guidelines

When creating a PR from an issue:

### Title Format
```
feat(package): Brief description (fixes #123)
```

### Body Template
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Manual testing completed
- [ ] CI passes

## Related
Fixes #123
```

### Commit Messages
```bash
# Feature
feat(extended-data-types): Add new utility function

# Bug fix
fix(vendor-connectors): Handle null response from API

# Documentation
docs(lifecyclelogging): Update README with examples

# Refactor
refactor(directed-inputs-class): Simplify validation logic
```

## Verification Before PR

Always run before creating PR:

```bash
# Python packages
cd packages/<package-name>
ruff check .
ruff format --check .
pytest

# TypeScript packages
cd packages/cursor-fleet
npm run build
npm test  # if tests exist
```

## Common Mistakes to Avoid

### ❌ Don't Suggest Version Changes
```python
# WRONG - Never touch this manually
__version__ = "2025.11.42"  # This is auto-generated
```

### ❌ Don't Add Unnecessary Dependencies
Check `extended-data-types` first before adding:
- `inflection` - already re-exported
- `orjson` - already re-exported  
- `ruamel.yaml` - already re-exported
- Custom JSON/YAML functions - use existing

### ❌ Don't Skip Tests
Every new function needs at least:
- Happy path test
- Edge case test (empty input, invalid input)

### ❌ Don't Ignore Type Hints
```python
# WRONG - Missing type hints
def process(data):
    return data

# CORRECT
def process(data: dict[str, Any]) -> dict[str, Any]:
    return data
```

## Integration with cursor-fleet

If you need to understand what previous agents did:

```bash
# Analyze a previous agent session
cursor-fleet analyze bc-xxx-xxx --output report.md

# Review code before pushing
cursor-fleet review --base main --head HEAD
```

## Questions?

- **Project Rules**: `.ruler/AGENTS.md`
- **Ecosystem Guide**: `.ruler/ecosystem.md`
- **Template Usage**: `TEMPLATE_USAGE.md`
- **Package Details**: `packages/*/README.md`

---

**Copilot Instructions Version:** 2.0
**Auto-Issue Compatible:** Yes
**Last Updated:** 2025-11-30
