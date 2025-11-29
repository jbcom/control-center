# FSC Control Center Coordination

## Overview

**FSC Control Center** is an enterprise counterparty to jbcom Control Center. FSC () uses jbcom Python packages in production infrastructure.

## Quick Reference

| Property | Value |
|----------|-------|
| Organization |  |
| Repository | `/fsc-control-center` |
| Role | Downstream consumer, upstream contributor |

## Packages FSC Uses

- **extended-data-types** - Config processing, type conversions
- **lifecyclelogging** - Structured logging in pipelines
- **vendor-connectors** - Cloud integrations (AWS, GCP)

## Recognizing FSC

### Issue Patterns
- Title: `🤖 FSC Feature Request: ...`
- Title: `🔄 Handoff from FSC: ...`
- Body: `From: FSC Control Center`

### PR Patterns
- Branch: `feat/fsc-*` or `fix/fsc-*`
- Body: `Contributed by FSC Control Center`

## Responding to FSC

### Feature Requests
```markdown
Thank you for the feature request from FSC Control Center.

Priority: <HIGH/MEDIUM/LOW>
Plan: <brief plan>

We'll update when work begins.
```

### Handoffs
```markdown
✅ Received by jbcom Control Center.

Understanding: <summary>
Timeline: <estimate>

Will comment when complete.
```

### Completion
```markdown
✅ Complete.

Released in: <package-name> v<YYYYMM.MINOR.PATCH>
PyPI: https://pypi.org/project/<package-name>/<YYYYMM.MINOR.PATCH>

FSC can now update dependencies.
```

## Station-to-Station

FSC operates autonomous agents. Communication is via GitHub issues:
1. FSC creates issue with context
2. jbcom acknowledges
3. jbcom completes work
4. jbcom comments results
5. FSC detects and continues

No human bottleneck required.

## Full Documentation

See: [Full Documentation](https://github.com/jbcom/jbcom-control-center/blob/main/docs/FSC-COUNTERPARTY-COORDINATION.md)

---

**Status**: Active  
**Established**: 2025-11-28
