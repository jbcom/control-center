---
mode: 'agent'
description: 'Automatically discover and inventory all jbcom repositories with dependency analysis'
tools:
  - github
---

# jbcom Repository Inventory

Perform a comprehensive inventory of all jbcom Python libraries.

## Steps

1. **Discover Repositories**
   - Query GitHub API for `org:jbcom language:Python`
   - List all repositories with basic info

2. **Analyze Each Repository**
   For each repository:
   - Read `pyproject.toml` to extract:
     - Package name
     - Version
     - Dependencies
     - Python version requirements
   - Check CI status from latest workflow run
   - Get latest PyPI release version
   - Count open issues and PRs
   - Identify primary maintainers

3. **Build Dependency Graph**
   - Map which libraries depend on which
   - Identify the dependency order (foundation → leaves)
   - Detect circular dependencies (should be none)

4. **Generate Report**
   Create a structured report with:

```markdown
# jbcom Python Library Ecosystem Inventory
**Generated:** [timestamp]

## Summary
- Total Repositories: X
- Production Ready: X
- In Development: X
- Total Dependencies: X

## Repository Details

### extended-data-types
- **PyPI:** extended-data-types==X.X.X
- **Latest Release:** YYYY.MM.BUILD
- **Status:** ✅ Production
- **CI:** ✅ Passing / ❌ Failing
- **Dependencies:** None (foundation)
- **Dependents:** [list]
- **Open Issues:** X
- **Open PRs:** X
- **Last Activity:** [date]

[Continue for each repository...]

## Dependency Graph

```
extended-data-types (foundation)
  ├── lifecyclelogging
  ├── directed-inputs-class
  └── vendor-connectors
       └── (uses lifecyclelogging)
```

## Health Indicators

### Security Alerts
[List any security alerts from Dependabot]

### Stale PRs (>30 days)
[List PRs needing attention]

### Failed CIs
[List repositories with failing CI]

### Version Mismatches
[Check if dependents use outdated versions]

## Recommended Actions

1. [Priority action items]
2. [...]
```

## Output

Present the full report in markdown format, ready to be saved to `ECOSYSTEM_INVENTORY.md`.

## Usage

```copilot
/jbcom-inventory

# Or with filters:
/jbcom-inventory status=production
/jbcom-inventory with-issues=true
```
