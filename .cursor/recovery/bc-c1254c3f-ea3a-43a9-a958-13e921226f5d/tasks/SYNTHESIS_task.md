📊 Forensic Recovery: Synthesis & Consolidation

## Context
You are the synthesis agent for recovery of failed agent **bc-c1254c3f-ea3a-43a9-a958-13e921226f5d**.

Multiple specialized sub-agents have analyzed different aspects:
- PR recovery agents
- Branch recovery agents

## Your Mission
Wait for all sub-agents to complete, then synthesize their findings.

### 1. Monitor Sub-Agent Progress
```bash
# Check for completed reports
ls -la /workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/reports/

# Read each report
for report in /workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/reports/*.md; do
  echo "=== $report ==="
  cat "$report"
  echo ""
done
```

### 2. Consolidate Findings
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/CONSOLIDATED_RECOVERY_REPORT.md`

Structure:
```markdown
# Forensic Recovery Report: Agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d

**Timestamp**: Thu Nov 27 05:51:03 UTC 2025
**Failed Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Status**: UNKNOWN
**Sub-Agents Deployed**: 22 PR agents + 1 branch agents

## Executive Summary
[High-level findings]

## PR Recovery Results
[Consolidate all PR_*_recovery.md files]

## Branch Recovery Results
[Consolidate all BRANCH_*_recovery.md files]

## Overall Assessment
- ✅ Work Completed: X items
- ⚠️ Work Partial: Y items
- ❌ Work Lost: Z items

## Recommendations
1. [Action item]
2. [Action item]

## GitHub Updates Needed
- [ ] Update issue #X
- [ ] Comment on PR #Y
- [ ] Close issue #Z

## Next Steps for Primary Agent
[Clear actions to take]
```

### 3. Update GitHub
- Create summary issue
- Update project board
- Link all related PRs/issues

---

**Wait for**: All sub-agent reports to be generated
**Output**: Consolidated recovery report + GitHub updates
