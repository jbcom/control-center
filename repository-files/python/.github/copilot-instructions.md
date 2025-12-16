# Python Copilot Instructions

## Python Environment

### Package Manager: uv (preferred) or pip
```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --extra tests  # REQUIRED for testing
uv sync --all-extras   # For all optional features
```

### Virtual Environment
```bash
# uv manages venv automatically, but if needed:
uv venv
source .venv/bin/activate
```

## Development Commands

### Testing (ALWAYS run tests)
```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test
uv run pytest tests/test_specific.py -v

# Run tests matching pattern
uv run pytest tests/ -v -k "test_pattern"
```

### Linting & Formatting
```bash
# Check linting (ruff)
uvx ruff check src/ tests/

# Auto-fix linting issues
uvx ruff check --fix src/ tests/

# Format code
uvx ruff format src/ tests/

# Type checking (if configured)
uv run mypy src/
```

### Building
```bash
uv build
```

## Code Patterns

### Imports
```python
# Standard library first
import os
from pathlib import Path

# Third-party
import pytest
from pydantic import BaseModel

# Local
from .module import function
```

### Type Hints (Required)
```python
def process_data(items: list[str], config: Config | None = None) -> dict[str, Any]:
    """Process items with optional config.
    
    Args:
        items: List of items to process
        config: Optional configuration
        
    Returns:
        Processed results
    """
    ...
```

### Error Handling
```python
from typing import Never

class ProcessingError(Exception):
    """Raised when processing fails."""
    pass

def process(data: str) -> Result:
    try:
        return do_processing(data)
    except ValueError as e:
        raise ProcessingError(f"Invalid data: {e}") from e
```

### Testing Patterns
```python
import pytest

class TestProcessor:
    """Tests for Processor class."""
    
    @pytest.fixture
    def processor(self) -> Processor:
        return Processor(config=test_config)
    
    def test_process_valid_input(self, processor: Processor) -> None:
        result = processor.process("valid")
        assert result.success is True
    
    def test_process_invalid_input_raises(self, processor: Processor) -> None:
        with pytest.raises(ProcessingError, match="Invalid"):
            processor.process("")
```

## Common Issues

### "Module not found"
```bash
# Ensure package is installed in editable mode
uv pip install -e .
```

### Tests not finding fixtures
```bash
# Ensure conftest.py is in tests/ directory
# Ensure __init__.py exists in test directories
```

### Import errors in tests
```python
# Use absolute imports from package root
from package_name.module import thing  # ✅
from .module import thing  # ❌ in tests
```

## File Structure
```
src/
├── package_name/
│   ├── __init__.py
│   ├── core.py
│   └── utils.py
tests/
├── __init__.py
├── conftest.py
└── test_core.py
pyproject.toml
```
