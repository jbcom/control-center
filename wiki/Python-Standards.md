# Python Standards

## Type Hints (Python 3.9+)

```python
# ✅ Modern style
def process(items: list[dict[str, Any]]) -> dict[str, int]:
    pass

# ❌ Old style
from typing import Dict, List
def process(items: List[Dict[str, Any]]) -> Dict[str, int]:
    pass
```

## Pathlib Over os.path

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
        items: List of dictionaries containing item data.
        validate: Whether to validate items before processing.

    Returns:
        Dictionary with processing summary and statistics.

    Raises:
        ValueError: If items list is empty.
    """
```

## Use extended-data-types First

```python
# ✅ Use foundation library
from extended_data_types import strtobool, make_raw_data_export_safe

# ❌ Don't reimplement
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

## Security - Sanitize Before Logging

```python
# ✅ Sanitize
from extended_data_types import make_raw_data_export_safe
safe = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe}")

# ❌ Never log raw data
logger.info(f"Processing: {user_data}")
```
