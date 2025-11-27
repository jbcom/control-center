# Repository Task: Vault/AWS

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 1
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 1 times.

## Files Mentioned
- README.md
- activeContext.md
- agenticRules.md
- aws_client.py
- github_client.py
- progress.md
- terraform_data_source.py
- terraform_null_resource.py
- utils.py

## PRs Mentioned
- #200
- #201
- #202

## Your Mission
1. Clone or access Vault/AWS
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view Vault/AWS --json name,description

# Check mentioned PRs
gh pr view 200 --repo Vault/AWS --json state,title
gh pr view 201 --repo Vault/AWS --json state,title
gh pr view 202 --repo Vault/AWS --json state,title

# Check files exist
ls -la README.md 2>/dev/null || echo 'Missing: README.md'
ls -la activeContext.md 2>/dev/null || echo 'Missing: activeContext.md'
ls -la agenticRules.md 2>/dev/null || echo 'Missing: agenticRules.md'
ls -la aws_client.py 2>/dev/null || echo 'Missing: aws_client.py'
ls -la github_client.py 2>/dev/null || echo 'Missing: github_client.py'
```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/Vault_AWS/RECOVERY_REPORT.md`
