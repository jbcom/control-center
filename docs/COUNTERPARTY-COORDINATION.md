# Counterparty Coordination: FSC ↔ jbcom Control Centers

## 🚨 NEW: Fleet Management Pattern (2025-11-28)

FSC Control Center now operates as a **control manager** using the Cursor API to:
1. **Spawn** dedicated agents in specific repositories
2. **Delegate** tasks to spawned agents
3. **Coordinate** via `addFollowup` API
4. **Enable diamond pattern** - agents communicate directly

### Quick Commands

```bash
# Spawn agent in terraform-modules
/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/FlipsideCrypto/terraform-modules \
    "Update vendor-connectors to 202511.7" main

# Spawn jbcom Control Center agent
/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/jbcom/jbcom-control-center \
    "Coordinate ecosystem release. Notify FSC agents when done." main

# Send update to spawned agent
/workspace/scripts/fleet-manager.sh followup bc-xxx "Package released, proceed"
```

See `docs/FLEET-MANAGEMENT-PROTOCOL.md` for full documentation.

---

## Overview

FSC Control Center and jbcom Control Center operate as **enterprise counterparties**, enabling:
- Automated package dependency management
- Cross-organization feature development
- Station-to-station agent handoffs
- Coordinated release management
- **Fleet management and agent spawning** (NEW)

## Control Center Registry

| Control Center | Organization | Repository | Primary Function |
|---------------|--------------|------------|------------------|
| **FSC Control Center** | FlipsideCrypto | `FlipsideCrypto/fsc-control-center` | Infrastructure pipeline orchestration |
| **jbcom Control Center** | jbcom | `jbcom/jbcom-control-center` | Python package ecosystem management |

## Token Configuration

### Environment Variables

```bash
# FSC operations (default in FSC context)
FLIPSIDE_GITHUB_TOKEN    # FlipsideCrypto org access

# jbcom operations (must be explicitly set)
GITHUB_JBCOM_TOKEN       # jbcom org access
```

### Authentication Patterns

```bash
# FSC repo operations (default)
gh pr list --repo FlipsideCrypto/terraform-modules

# jbcom repo operations (ALWAYS prefix)
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr list --repo jbcom/jbcom-control-center
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api /repos/jbcom/extended-data-types/releases

# Cross-org cloning
GH_TOKEN="$GITHUB_JBCOM_TOKEN" git clone https://$GITHUB_JBCOM_TOKEN@github.com/jbcom/jbcom-control-center.git
```

## Coordination Workflows

### 1. Dependency Update Flow (jbcom → FSC)

When jbcom releases a new package version:

```
┌─────────────────────┐    Release    ┌─────────────────────┐
│  jbcom Control      │──────────────►│  PyPI               │
│  Center             │               │  (public)           │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                                 ▼
┌─────────────────────┐    Update     ┌─────────────────────┐
│  FSC Control        │◄──────────────│  Dependabot/Agent   │
│  Center             │               │  Detection          │
└─────────────────────┘               └─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  terraform-modules  │
│  (uses packages)    │
└─────────────────────┘
```

**Agent Action:**
```bash
# 1. Check for updates
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release list --repo jbcom/extended-data-types --limit 5

# 2. Review what changed
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release view <tag> --repo jbcom/extended-data-types --json body

# 3. Update FSC dependencies
# Create PR in terraform-modules with updated versions

# 4. Log coordination
echo "## Dependency Update $(date)" >> memory-bank/progress.md
echo "- Updated extended-data-types to X.Y.Z" >> memory-bank/progress.md
```

### 2. Feature Request Flow (FSC → jbcom)

When FSC needs a feature in jbcom packages:

```
┌─────────────────────┐   Feature    ┌─────────────────────┐
│  FSC Control        │───Request───►│  jbcom Control      │
│  Center             │              │  Center             │
└─────────────────────┘              └─────────────────────┘
        │                                     │
        │ Track Issue                         │ Implement
        ▼                                     ▼
┌─────────────────────┐              ┌─────────────────────┐
│  FSC GitHub Issues  │              │  jbcom packages/    │
│  (tracking)         │              │  (development)      │
└─────────────────────┘              └─────────────────────┘
                                              │
                                              │ Release
                                              ▼
                                     ┌─────────────────────┐
                                     │  PyPI               │
                                     └─────────────────────┘
```

**Agent Action:**
```bash
# 1. Create issue in jbcom
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create \
  --repo jbcom/jbcom-control-center \
  --title "🤖 FSC Feature Request: <feature>" \
  --body "## From: FSC Control Center

**Requesting Repo**: FlipsideCrypto/terraform-modules
**Package**: extended-data-types
**Priority**: MEDIUM

## Feature Request
<detailed description>

## Use Case
<why FSC needs this>

## Proposed Implementation
<optional suggestions>

---
*Created by FSC Control Center background agent*
*Coordination: station-to-station protocol*"

# 2. Track locally
gh issue create \
  --repo FlipsideCrypto/fsc-control-center \
  --title "🔗 Tracking: jbcom feature request" \
  --body "Tracking jbcom/jbcom-control-center#<issue_number>"
```

### 3. Upstream Contribution Flow (FSC → jbcom)

When FSC contributes code to jbcom:

```bash
# 1. Clone jbcom control center
cd /tmp
GH_TOKEN="$GITHUB_JBCOM_TOKEN" git clone https://$GITHUB_JBCOM_TOKEN@github.com/jbcom/jbcom-control-center.git
cd jbcom-control-center

# 2. Create feature branch
git checkout -b feat/fsc-contribution-<name>

# 3. Make changes following jbcom conventions
# - Use conventional commits: feat(scope): description
# - Scopes: edt, logging, dic, connectors
# - Follow CalVer versioning

# 4. Create PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --title "feat(edt): <description>" \
  --body "## Summary
<description>

## From FSC Control Center
This contribution addresses a need identified in FlipsideCrypto infrastructure.

## Test Plan
- [ ] Unit tests pass
- [ ] Lint passes (ruff)
- [ ] Type check passes (mypy)

## FSC Integration
Will be consumed by terraform-modules after release."

# 5. Track in FSC
gh issue create \
  --repo FlipsideCrypto/fsc-control-center \
  --title "🔗 Upstream PR: jbcom/jbcom-control-center#<pr_number>" \
  --body "Tracking upstream contribution"
```

## Inter-Control-Center Handoff

### When to Hand Off to jbcom

Hand off to jbcom control center when:
- Feature requires jbcom package changes
- Bug is in jbcom package, not FSC code
- Release coordination needed

### Handoff Protocol

```bash
# 1. Document handoff in FSC
cat >> memory-bank/activeContext.md << 'EOF'

## Handoff to jbcom Control Center
**Date**: $(date +%Y-%m-%d)
**Reason**: <reason>
**jbcom Issue/PR**: <link>
**Expected Return**: <when FSC should check back>
EOF

# 2. Create jbcom issue/PR with context
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create \
  --repo jbcom/jbcom-control-center \
  --title "🔄 Handoff from FSC: <task>" \
  --body "## Station-to-Station Handoff

**From**: FSC Control Center
**Repository**: FlipsideCrypto/fsc-control-center
**Branch**: <branch>

## Context
<full context>

## Requested Action
<what jbcom agent should do>

## Return Protocol
After completion, please:
1. Comment on this issue with results
2. FSC agent will detect and continue

---
*Station-to-station handoff from FSC Control Center*"

# 3. Set reminder to check back
echo "Check jbcom issue #<number> on $(date -d '+3 days' +%Y-%m-%d)" >> memory-bank/activeContext.md
```

## Monitoring and Observability

### Check Counterparty Status

```bash
# jbcom control center health
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api /repos/jbcom/jbcom-control-center --jq '{
  open_issues: .open_issues_count,
  default_branch: .default_branch,
  pushed_at: .pushed_at
}'

# Recent jbcom releases
for pkg in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  echo "=== $pkg ==="
  GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh release list --repo jbcom/$pkg --limit 3
done

# Open PRs in jbcom
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr list --repo jbcom/jbcom-control-center --state open
```

### Check for Pending Coordination

```bash
# FSC issues referencing jbcom
gh issue list --label "jbcom" --state open

# Search for coordination notes
grep -r "jbcom" memory-bank/

# Check for handoff markers
grep -r "Handoff to jbcom" memory-bank/
```

## Emergency Procedures

### jbcom Token Not Working

```bash
# 1. Verify token exists
echo "Token exists: $([ -n "$GITHUB_JBCOM_TOKEN" ] && echo 'YES' || echo 'NO')"

# 2. Test token
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh auth status

# 3. If token invalid, document and escalate
gh issue create \
  --repo FlipsideCrypto/fsc-control-center \
  --title "🚨 GITHUB_JBCOM_TOKEN Invalid" \
  --body "Token is not working. Human intervention required."
```

### jbcom Package Breaking Change

```bash
# 1. Document the issue
gh issue create \
  --title "🚨 jbcom Package Breaking Change" \
  --body "Package X version Y.Z introduced breaking change.

## Impact
- Affected FSC repos: <list>
- Error: <error message>

## Mitigation
- Pinned to previous version: X.Y.Z-1
- Opened issue in jbcom: <link>"

# 2. Pin to previous version
# Update requirements/pyproject.toml to pin version

# 3. Notify jbcom
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create \
  --repo jbcom/jbcom-control-center \
  --title "🐛 Breaking change in <package> X.Y.Z" \
  --body "## Report from FSC Control Center

Breaking change detected in <package> version X.Y.Z

## Error
\`\`\`
<error message>
\`\`\`

## FSC Impact
<description>

## Request
Please review and advise on migration path or fix."
```

## Best Practices

### DO

- ✅ Always use `GITHUB_JBCOM_TOKEN` for jbcom operations
- ✅ Document all cross-control-center coordination in memory-bank
- ✅ Create tracking issues when handing off
- ✅ Follow jbcom conventions when contributing upstream
- ✅ Test integrations before merging dependency updates

### DON'T

- ❌ Assume FSC token works for jbcom repos
- ❌ Make jbcom changes without following their conventions
- ❌ Hand off without documenting context
- ❌ Ignore jbcom package changelogs when updating

---

**Last Updated**: 2025-11-28  
**Protocol Version**: 1.0  
**Status**: Active
