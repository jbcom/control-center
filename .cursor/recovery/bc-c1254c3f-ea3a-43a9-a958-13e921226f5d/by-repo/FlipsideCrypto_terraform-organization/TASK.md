# Repository Task: FlipsideCrypto/terraform-organization

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 2
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 2 times.

## Files Mentioned


## PRs Mentioned
- #168
- #205
- #43

## Your Mission
1. Clone or access FlipsideCrypto/terraform-organization
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view FlipsideCrypto/terraform-organization --json name,description

# Check mentioned PRs
gh pr view 168 --repo FlipsideCrypto/terraform-organization --json state,title
gh pr view 205 --repo FlipsideCrypto/terraform-organization --json state,title
gh pr view 43 --repo FlipsideCrypto/terraform-organization --json state,title

# Check files exist

```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/FlipsideCrypto_terraform-organization/RECOVERY_REPORT.md`
