# Python Standards

## Type Hints (Python 3.9+)

```python
# ✅ Modern style
def process(items: list[dict[str, Any]]) -> dict[str, int]:
    pass

# ❌ Old style - don't use
from typing import Dict, List
def process(items: List[Dict[str, Any]]) -> Dict[str, int]:
    pass
```

## Pathlib Over os.path

```python
# ✅ Use pathlib
from pathlib import Path
config = Path("config.yaml")
if config.exists():
    content = config.read_text()

# ❌ Avoid os.path
import os
config = os.path.join("config.yaml")
if os.path.exists(config):
    with open(config) as f:
        content = f.read()
```

## Docstrings (Google Style)

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
        >>> items = [{"id": 1, "name": "test"}]
        >>> process_items(items)
        {"count": 1, "valid": 1}
    """
```

## Error Messages

```python
# ✅ Helpful - context and solution
if not config_file.exists():
    raise FileNotFoundError(
        f"Config not found: {config_file}. "
        f"Create with: python setup.py init"
    )

# ❌ Vague - no context
raise FileNotFoundError("Config not found")
```

## Testing

```python
# ✅ Descriptive names, clear assertions
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ❌ Vague name, unclear assertions
def test_stuff():
    assert process_data([{"id": 1}])
```

## Use extended-data-types

Always check the foundation library first:

```python
# ✅ Use existing utilities
from extended_data_types import (
    strtobool,
    make_raw_data_export_safe,
    encode_json,
    decode_yaml,
)

# ❌ Don't reimplement
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

## Security

```python
# ✅ Sanitize before logging
from extended_data_types import make_raw_data_export_safe
safe = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe}")

# ❌ Never log raw user data
logger.info(f"Processing: {user_data}")  # May contain secrets!
```
