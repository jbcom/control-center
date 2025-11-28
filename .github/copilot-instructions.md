# GitHub Copilot Instructions

> **📚 Full documentation**: https://github.com/jbcom/jbcom-control-center/wiki/Agent-Instructions-Copilot

## Quick Rules

- **Versioning**: `YYYYMM.MINOR.PATCH` via python-semantic-release
- **Commits**: Use conventional commits with scopes (`edt`, `logging`, `dic`, `connectors`)
- **Git tags**: Track release state per package (required)

## Commit Format

```bash
feat(edt): add new utility       # Minor bump
fix(logging): handle edge case   # Patch bump
feat!: breaking change           # Major bump
```

## Code Style

```python
# Modern type hints
def func(data: dict[str, Any]) -> list[str]: ...

# Use pathlib
from pathlib import Path

# Use extended-data-types
from extended_data_types import strtobool
```

See [wiki](https://github.com/jbcom/jbcom-control-center/wiki/Agent-Instructions-Copilot) for full instructions.
