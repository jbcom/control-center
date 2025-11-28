# Python Standards

## Type Hints

```python
# ✅ Modern style (Python 3.9+)
def process(items: list[dict[str, Any]]) -> dict[str, int]:
    pass

# ❌ Old style
from typing import Dict, List
def process(items: List[Dict[str, Any]]) -> Dict[str, int]:
    pass
```

## Pathlib

```python
# ✅ Use pathlib
from pathlib import Path
config = Path("config.yaml")

# ❌ Avoid os.path
import os
config = os.path.join("config.yaml")
```

## Docstrings (Google Style)

```python
def process_items(items: list[dict], validate: bool = True) -> dict[str, Any]:
    """Process a list of items and return summary.

    Args:
        items: List of dictionaries containing item data
        validate: Whether to validate items before processing

    Returns:
        Dictionary with processing summary and statistics

    Raises:
        ValueError: If items list is empty
    """
```

## Error Messages

```python
# ✅ Helpful
if not config_file.exists():
    raise FileNotFoundError(
        f"Config not found: {config_file}. "
        f"Create with: python setup.py init"
    )

# ❌ Vague
raise FileNotFoundError("Config not found")
```

## Testing

```python
# ✅ Descriptive names, clear assertions
def test_process_data_returns_correct_count():
    items = [{"id": 1}, {"id": 2}]
    result = process_data(items)
    assert result["count"] == 2

# ❌ Vague
def test_stuff():
    assert process_data([{"id": 1}])
```

## Dependencies

**Always check extended-data-types first:**

```python
# ✅ Use foundation library
from extended_data_types import strtobool, make_raw_data_export_safe

# ❌ Don't reimplement
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```
