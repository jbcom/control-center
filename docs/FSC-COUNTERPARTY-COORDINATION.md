# FSC Control Center - Counterparty Coordination

## Overview

**FSC Control Center** (/fsc-control-center) is an enterprise counterparty that:
- Consumes jbcom Python packages in production infrastructure
- May contribute features upstream to jbcom packages
- Coordinates package updates and releases
- Operates autonomous background agents

## FSC Control Center Details

| Property | Value |
|----------|-------|
| Organization |  |
| Repository | `/fsc-control-center` |
| Primary Function | Terraform pipeline orchestration |
| Packages Used | extended-data-types, lifecyclelogging, vendor-connectors |

## jbcom Packages Used by FSC

FSC uses these packages in their `terraform-modules` repository:

| Package | FSC Use Case |
|---------|--------------|
| `extended-data-types` | Config processing, type conversions, serialization |
| `lifecyclelogging` | Structured logging in pipeline workflows |
| `vendor-connectors` | AWS, GCP integrations for infrastructure |

## Recognizing FSC Interactions

### FSC-Created Issues

FSC Control Center creates issues with these patterns:
- **Title prefix**: `🤖 FSC Feature Request:`
- **Title prefix**: `🔄 Handoff from FSC:`
- **Body contains**: `From: FSC Control Center`

### FSC-Created PRs

FSC contributes PRs with:
- **Branch pattern**: `feat/fsc-*` or `fix/fsc-*`
- **Body contains**: `Contributed by FSC Control Center`
- **Follows**: jbcom conventions (conventional commits, CalVer)

### FSC Handoffs

When FSC hands off work to jbcom:
- Issue title: `🔄 Handoff from FSC: <task>`
- Body includes full context from FSC side
- Expects acknowledgment and response

## Responding to FSC

### Feature Requests

When FSC creates a feature request:

```markdown
Thank you for the feature request from FSC Control Center.

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
<summarize what FSC needs>

**Plan:**
<what jbcom will do>

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
- Version: <YYYYMM.MINOR.PATCH>
- PyPI: https://pypi.org/project/<package-name>/<YYYYMM.MINOR.PATCH>

FSC can now update their dependencies to use this version.
```

## Coordination Workflows

### Package Release Impact

When releasing packages that FSC uses:
1. Note breaking changes in release notes
2. Document migration paths for breaking changes
3. Consider tagging FSC in discussions for major updates

### Reviewing FSC Contributions

When FSC submits a PR:
1. Review within 48 hours
2. Apply standard review process
3. Acknowledge FSC use case context in review
4. After merge, comment on any related FSC issues

### Cross-Organization Communication

- Use GitHub issues for all coordination (public, traceable)
- Reference issues across repos when relevant
- Keep context in issues for future agents

## Labels (Recommended)

Consider using these labels for FSC-related items:
- `fsc` - Related to FSC Control Center
- `counterparty` - Cross-organization coordination
- `downstream-consumer` - From a package consumer

## Station-to-Station Protocol

FSC Control Center operates autonomous agents that can:
- Create issues and PRs
- Respond to feedback
- Complete work without human intervention

When FSC hands off work to jbcom:
1. FSC creates issue with full context
2. jbcom agent acknowledges receipt
3. jbcom completes work
4. jbcom comments with results
5. FSC detects completion and continues

This enables seamless cross-organization coordination without human bottlenecks.

## Emergency Escalation

For urgent issues requiring immediate human attention:
- FSC will create issue with `🚨 URGENT` prefix
- Tag maintainers directly
- Provide full context of urgency

---

**Protocol Version**: 1.0  
**Established**: 2025-11-28  
**FSC Repository**: /fsc-control-center
