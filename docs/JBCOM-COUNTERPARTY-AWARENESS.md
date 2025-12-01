# jbcom Control Center - FSC Counterparty Awareness

> **This document should be added to jbcom-control-center to enable bidirectional awareness.**

## For jbcom Agents: Understanding FSC

### Who is FSC?

**FSC Control Center** (FlipsideCrypto/fsc-control-center) is an enterprise counterparty that:
- Consumes jbcom Python packages in production
- May contribute features upstream
- Coordinates package updates and releases
- Operates autonomous background agents

### FSC Repository

| Property | Value |
|----------|-------|
| Organization | FlipsideCrypto |
| Repository | fsc-control-center |
| Primary Use | Terraform pipeline orchestration |
| Token Required | `GITHUB_FSC_TOKEN` (if accessing FSC repos) |

### jbcom Packages Used by FSC

FSC uses these packages in `terraform-modules`:
- `extended-data-types` - Config processing, type conversions
- `lifecyclelogging` - Structured logging in pipelines
- `vendor-connectors` - AWS, GCP integrations

## Recognizing FSC Interactions

### FSC Issues

FSC creates issues with these patterns:
- Title: `🤖 FSC Feature Request: ...`
- Title: `🔄 Handoff from FSC: ...`
- Body contains: `From: FSC Control Center`

### FSC PRs

FSC contributes PRs with:
- Branch pattern: `feat/fsc-*` or `fix/fsc-*`
- Body contains: `Contributed by FSC Control Center`
- Uses proper jbcom conventions

### FSC Handoffs

When FSC hands off work to jbcom:
- Issue title: `🔄 Handoff from FSC: <task>`
- Body includes full context
- Expects response within 48h

## How to Respond to FSC

### Feature Requests

When FSC requests a feature:

```markdown
@fsc-control-center Thank you for the feature request.

**Assessment:**
- Priority: <HIGH/MEDIUM/LOW>
- Estimated effort: <timeframe>
- Breaking changes: <YES/NO>

**Plan:**
1. <step 1>
2. <step 2>

We'll update this issue when work begins.
```

### Handoff Acknowledgment

When receiving a handoff from FSC:

```markdown
✅ Received by jbcom Control Center.

**Understanding:**
<summarize the request>

**Plan:**
<what you'll do>

**Timeline:**
<expected completion>

Will comment when complete.
```

### After Completing FSC-Related Work

```markdown
✅ Complete.

**Changes Made:**
- <change 1>
- <change 2>

**Released In:**
- Package: <package-name>
- Version: <version>
- PyPI: https://pypi.org/project/<package>/<version>

FSC can now update their dependencies to use this version.
```

## Coordination Protocols

### Package Release Impact on FSC

When releasing packages that FSC uses:
1. Note breaking changes prominently
2. Document migration paths
3. Consider creating FSC-specific issue if major changes

### Responding to FSC Contributions

When FSC submits a PR:
1. Review within 48h
2. Follow normal review process
3. Acknowledge FSC use case in merge commit
4. Tag FSC issue if one exists

### Cross-Control-Center Communication

For complex coordination:
1. Use GitHub issues for async communication
2. Reference issues across repos when needed
3. Keep conversation in public for traceability

## Issue/PR Labels

Consider adding these labels for FSC coordination:
- `fsc` - Related to FSC Control Center
- `counterparty` - Cross-organization coordination
- `upstream-contribution` - Contributed by downstream consumer

## Wiki Page (Recommended)

Add a wiki page: `FSC-Control-Center-Coordination`

Content:
```markdown
# FSC Control Center Coordination

## Overview
FSC Control Center (FlipsideCrypto/fsc-control-center) is a primary consumer of jbcom packages.

## Current Status
- Last coordination: <date>
- Open FSC issues: <count>
- Open FSC PRs: <count>

## Packages FSC Uses
- extended-data-types
- lifecyclelogging
- vendor-connectors

## Contact
FSC operates autonomous agents. Communication via GitHub issues.
```

## Emergency Contact

For urgent issues requiring human attention:
- Create issue with `🚨 URGENT` prefix
- Tag appropriate maintainers

---

**This document enables jbcom agents to understand and respond to FSC Control Center interactions appropriately.**
