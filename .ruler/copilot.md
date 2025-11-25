# GitHub Copilot Specific Configuration

Quick reference for GitHub Copilot when working in this template or managed repositories.

## Quick Rules - Read First! 🚨

### CalVer Auto-Versioning
✅ Version is automatic: `YYYY.MM.BUILD`
❌ Never suggest: semantic-release, git tags, manual versioning

### Release Process
✅ Every main push = PyPI release (automatic)
❌ Never suggest: conditional releases, manual steps

### Code Quality
✅ Type hints required
✅ Tests for new features
✅ Ruff for linting/formatting
❌ Don't add complexity

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

### Type Hints
```python
# ✅ Good - complete type hints
def process_data(items: list[dict[str, Any]]) -> dict[str, int]:
    """Process items and return counts."""
    return {"count": len(items)}

# ❌ Avoid - no type hints
def process_data(items):
    return {"count": len(items)}
```

## Testing Patterns

### Write Clear Tests
```python
# ✅ Good - descriptive name, clear assertion
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ❌ Avoid - vague name, multiple assertions
def test_stuff():
    result = process_data([{"id": 1}])
    assert result
    assert "count" in result
    assert result["count"] > 0
```

### Use Fixtures
```python
# ✅ Good - reusable setup
@pytest.fixture
def sample_data():
    return [{"id": i} for i in range(10)]

def test_with_fixture(sample_data):
    result = process_data(sample_data)
    assert result["count"] == 10
```

## When Working in Ecosystem

### Using extended-data-types
If the library depends on extended-data-types, use its utilities:

```python
# ✅ Good - use existing utilities
from extended_data_types import (
    get_unique_signature,
    make_raw_data_export_safe,
    strtobool,
)

# ❌ Avoid - reimplementing
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

### Data Sanitization
Always sanitize before logging/exporting:

```python
# ✅ Good
from extended_data_types import make_raw_data_export_safe
safe_data = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe_data}")

# ❌ Avoid - logging raw data
logger.info(f"Processing: {user_data}")  # might have secrets!
```

## Common Tasks

### Adding a New Function
1. Write the function with type hints
2. Add docstring (Google style)
3. Write tests (at least happy path + edge cases)
4. Update module `__all__` if public API
5. Run `ruff check` and `pytest`

### Fixing a Bug
1. Write a test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Check for similar bugs
5. Update documentation if needed

### Refactoring
1. Ensure tests exist and pass
2. Make changes incrementally
3. Run tests after each change
4. Verify type checking still passes
5. Update docstrings if behavior changed

## Error Messages

### Be Helpful
```python
# ✅ Good - clear error with context
if not config_file.exists():
    raise FileNotFoundError(
        f"Config file not found: {config_file}. "
        f"Create it with: python setup.py init"
    )

# ❌ Avoid - vague error
if not config_file.exists():
    raise FileNotFoundError("Config not found")
```

## Documentation

### Docstring Format (Google Style)
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
        
    Example:
        >>> items = [{"id": 1, "name": "Item 1"}]
        >>> process_items(items)
        {"count": 1, "valid": 1}
    """
```

## Performance Tips

### Avoid Repeated Computation
```python
# ✅ Good - compute once
unique_items = set(items)
for item in unique_items:
    process(item)

# ❌ Avoid - computing in loop
for item in items:
    if item not in processed:  # O(n) lookup each time
        process(item)
```

### Use Appropriate Data Structures
```python
# ✅ Good - O(1) lookup
seen = set()
for item in items:
    if item not in seen:
        seen.add(item)

# ❌ Avoid - O(n) lookup
seen = []
for item in items:
    if item not in seen:  # Slow for large lists
        seen.append(item)
```

## Security

### Never Log Secrets
```python
# ✅ Good - sanitize before logging
safe_config = {k: v for k, v in config.items() if k != "api_key"}
logger.info(f"Config: {safe_config}")

# ❌ Avoid - might log secrets
logger.info(f"Config: {config}")
```

### Validate Input
```python
# ✅ Good - validate before use
def load_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.is_file():
        raise ValueError(f"Not a file: {filepath}")
    if not path.suffix == ".json":
        raise ValueError(f"Not a JSON file: {filepath}")
    return path.read_text()
```

## Questions?

- Check `.ruler/AGENTS.md` for comprehensive guide
- Check `TEMPLATE_USAGE.md` for template setup
- Check `README.md` for project overview
- Don't suggest changes to CalVer/versioning approach

---

**Copilot Instructions Version:** 1.0
**Compatible With:** GitHub Copilot, Copilot Chat
**Last Updated:** 2025-11-25
