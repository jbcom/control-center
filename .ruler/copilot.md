# GitHub Copilot Configuration

Quick reference for GitHub Copilot when working in jbcom-control-center.

## Quick Rules 🚨

### Versioning - Python Semantic Release
✅ Uses conventional commits (`feat:`, `fix:`)
✅ Creates per-package git tags
✅ CalVer-style format: `YYYYMM.MINOR.PATCH`

### Release Process
✅ Merge to main triggers release analysis
✅ `feat:` → minor bump, `fix:` → patch bump
✅ `chore:`, `docs:` → no release

### Code Quality
✅ Type hints required
✅ Tests for new features
✅ Ruff for linting/formatting

## Commit Message Format

**REQUIRED for releases to work:**

```bash
# Feature (minor bump)
feat(edt): add new utility function

# Fix (patch bump)  
fix(vc): resolve authentication bug

# Breaking change (major bump)
feat(dic)!: remove deprecated API

# No release
docs: update README
chore: update dependencies
```

### Package Scopes
- `edt` = extended-data-types
- `ll` = lifecyclelogging
- `dic` = directed-inputs-class
- `vc` = vendor-connectors
- `ptb` = python-terraform-bridge

## Code Patterns

### Prefer Modern Python
```python
# ✅ Good - modern type hints
from collections.abc import Mapping
def func(data: dict[str, Any]) -> list[str]:
    pass

# ❌ Avoid - old style
from typing import Dict, List
def func(data: Dict[str, Any]) -> List[str]:
    pass
```

### Use Pathlib
```python
# ✅ Good
from pathlib import Path
config_file = Path("config.yaml")

# ❌ Avoid
import os
config_file = os.path.join("config.yaml")
```

### Type Hints Required
```python
# ✅ Good
def process_data(items: list[dict[str, Any]]) -> dict[str, int]:
    """Process items and return counts."""
    return {"count": len(items)}

# ❌ Avoid
def process_data(items):
    return {"count": len(items)}
```

## Testing Patterns

### Write Clear Tests
```python
# ✅ Good - descriptive name
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ❌ Avoid - vague name
def test_stuff():
    result = process_data([{"id": 1}])
    assert result
```

### Use Fixtures
```python
@pytest.fixture
def sample_data():
    return [{"id": i} for i in range(10)]

def test_with_fixture(sample_data):
    result = process_data(sample_data)
    assert result["count"] == 10
```

## Common Tasks

### Adding a New Function
1. Write function with type hints
2. Add docstring (Google style)
3. Write tests
4. Update module `__all__` if public API
5. Run `ruff check` and `pytest`
6. Commit with `feat(scope):` message

### Fixing a Bug
1. Write test that reproduces bug
2. Fix the bug
3. Verify test passes
4. Commit with `fix(scope):` message

## Documentation - Google Style
```python
def process_items(items: list[dict], validate: bool = True) -> dict[str, Any]:
    """Process a list of items and return summary.

    Args:
        items: List of dictionaries containing item data
        validate: Whether to validate items before processing

    Returns:
        Dictionary with processing summary and statistics

    Raises:
        ValueError: If items list is empty or validation fails
    """
```

## Security

### Never Log Secrets
```python
# ✅ Good
safe_config = {k: v for k, v in config.items() if k != "api_key"}
logger.info(f"Config: {safe_config}")

# ❌ Avoid
logger.info(f"Config: {config}")
```

---

**Copilot Instructions Version:** 2.0
**Last Updated:** 2025-11-30
