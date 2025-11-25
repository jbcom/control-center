---
description: 'Instructions for managing Python libraries in the jbcom ecosystem'
applyTo: '**/*.py, **/pyproject.toml, **/tox.ini'
---

# jbcom Python Library Management

## Ecosystem-Specific Guidelines

### When Working in jbcom Repositories

1. **Check which repository you're in**:
   - extended-data-types: Foundation library - extra caution required
   - lifecyclelogging: Production logging library
   - directed-inputs-class: Input validation (in development)
   - vendor-connectors: Service integrations (planning)
   - python-library-template: Template repository

2. **Dependency Management**:
   - **ALWAYS** use extended-data-types utilities when available
   - Don't reimplement functionality that exists in extended-data-types
   - Keep dependencies minimal
   - Use version ranges: `extended-data-types>=2025.11.0`

3. **Release Coordination**:
   - If updating extended-data-types, coordinate releases of dependents
   - Release in dependency order: foundation → dependents
   - Wait ~5 minutes for PyPI availability between releases

### Version Management

All jbcom libraries use CalVer (YYYY.MM.BUILD):
- Auto-generated on every main branch push
- No manual version management
- No git tags
- PyPI is the source of truth

### Code Patterns

#### Using extended-data-types
```python
# ✅ Good - use existing utilities
from extended_data_types import (
    get_unique_signature,
    make_raw_data_export_safe,
    strtobool,
    strtopath,
)

# ❌ Avoid - reimplementing
def my_str_to_bool(val: str) -> bool:
    return val.lower() in ("true", "yes", "1")
```

#### Data Sanitization
```python
# ✅ Good - sanitize before logging
from extended_data_types import make_raw_data_export_safe

safe_data = make_raw_data_export_safe(user_data)
logger.info(f"Processing: {safe_data}")

# ❌ Avoid - logging potentially sensitive data
logger.info(f"Processing: {user_data}")
```

#### Type Hints
```python
# ✅ Good - modern type hints
from collections.abc import Mapping
def process(data: dict[str, Any]) -> list[str]:
    pass

# ❌ Avoid - old style
from typing import Dict, List
def process(data: Dict[str, Any]) -> List[str]:
    pass
```

### Testing

#### Required Test Coverage
- extended-data-types: 100% (foundation library)
- Other libraries: ≥80%

#### Test Patterns
```python
# ✅ Good - descriptive, focused
def test_make_raw_data_export_safe_removes_credentials():
    data = {"user": "alice", "password": "secret"}
    result = make_raw_data_export_safe(data)
    assert "password" not in result

# ❌ Avoid - vague, multiple assertions
def test_sanitize():
    result = sanitize(data)
    assert result
    assert "password" not in result
    assert len(result) > 0
```

### Cross-Repository Changes

When making changes that affect multiple repositories:

1. **Start with extended-data-types** (if applicable)
2. **Test in one dependent** repository first
3. **Create PRs in dependency order**
4. **Link PRs together** in descriptions
5. **Don't merge** until all PRs ready
6. **Release in order**: extended-data-types → dependents

### CI/CD

All jbcom libraries use the same CI workflow:
- Tests across Python 3.10, 3.11, 3.12, 3.13
- Type checking with pyright
- Linting with ruff
- Coverage reporting
- Auto-versioning on main
- PyPI publishing

### Documentation

#### README Requirements
- Quick start section
- Installation instructions
- Basic usage examples
- Link to API documentation
- Mention ecosystem position

#### Docstrings (Google Style)
```python
def process_data(items: list[dict], validate: bool = True) -> dict[str, Any]:
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
        >>> process_data(items)
        {"count": 1, "valid": 1}
    """
```

### Security

- **Never log secrets** - always sanitize with make_raw_data_export_safe
- **Validate all inputs** - especially from external sources
- **Use Dependabot** - all repos have automated security updates
- **Update promptly** - security updates take priority

### Performance

- **Minimize dependencies** - keep install time fast
- **Lazy imports** - import heavy dependencies only when needed
- **Profile changes** - ensure no regressions in hot paths
- **Document complexity** - note O(n²) or similar

### Breaking Changes

If you must introduce a breaking change:

1. **Discuss in issue first** - get consensus
2. **Document migration path** - clear upgrade guide
3. **Update all dependents** - coordinate ecosystem-wide
4. **Update CHANGELOG.md** - mark as breaking
5. **Consider deprecation period** - warn before removing

## Ecosystem-Aware Prompts

When working in jbcom repositories, Copilot should:

- **Suggest extended-data-types** when you're reimplementing common utilities
- **Check dependency versions** before adding new dependencies
- **Validate test coverage** meets repository requirements
- **Remind about sanitization** when logging user data
- **Suggest ecosystem coordination** for cross-cutting changes

---

**These instructions apply automatically to all Python files and configuration files in jbcom repositories.**
