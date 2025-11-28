# GitHub Copilot Instructions

> **📚 Full documentation**: https://github.com/jbcom/jbcom-control-center/wiki/Agent-Instructions-Copilot

## Quick Rules

- **CalVer**: `YYYY.MM.BUILD` - automatic, never manual
- **NO semantic-release** - We use CalVer
- **NO git tags** - PyPI is source of truth

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
