# Active Context

## Current Focus
- Merge Cursor and repository memory banks into the root-level `memory-bank/` without symlinks.
- Automate replay of background agent sessions into the shared memory bank and delegation prompts.

## Active Work

### Session Replay Automation
- Replayed recent background agent session into the recovery archive and appended its summary to the progress log.
- Captured delegation inputs for MCP-aware CLIs to spawn focused sub-agents.

## Next Actions
- Run `python scripts/replay_agent_session.py --conversation <path/to/conversation.json>` for each new recovery export.
- Check `memory-bank/recovery/` for delegation prompts to pipe into MCP-aware CLIs (Codex, Claude code aider).
- Keep `memory-bank/` and `.cursor/memory-bank/` synchronized after each replay using this script's mirroring step.

## Session Highlight
Now let me provide a summary of the proper solution:

---

## ✅ Proper Enterprise Secrets Sync Solution

### The Problem (What You Identified)
The SSH key issue wasn't about SSH vs HTTPS - it was about **where we read secrets from**:
- `toJson(secrets)` in GitHub Actions only exposes secrets the workflow has access to
- `EXTERNAL_CI_BOT_SSH_PRIVATE_KEY` has **PRIVATE** visibility → not accessible
- Hacking around with HTTPS+token created complexity elsewhere

### The Proper Solution
**Read from SOURCE (SOPS files) using the same AWS auth pattern that's already working**

```
┌────────────────────────────────────────┐
│  workspaces/secrets/secrets/           │
│  ├── vendors.json  (SOPS encrypted)    │
│  ├── quay-credentials.yaml             │
│  ├── snowflake_tf_snow_key.pem         │
│  └── ...                               │
└────────────────────────────────────────┘
           │
           │ Decrypt via AWS KMS
           │ (same auth as generator/secrets jobs)
           ▼
┌────────────────────────────────────────┐
│  sync-enterprise-secrets action        │
│  - sops-decoder (npm package)          │
│  - @aws-sdk/client-kms                 │
│  - libsodium (GitHub secret encrypt)   │
└────────────────────────────────────────┘
           │
           │ GitHub API
           ▼
┌────────────────────────────────────────┐
│  Target Organizations                  │
│  -  │
│  - (other enterprise orgs)             │
└────────────────────────────────────────┘
```

### What Was Created

**1. JavaScript GitHub Action**: `.github/actions/sync-enterprise-secrets/`
- Uses `sops-decoder` to decrypt SOPS files via AWS KMS
- Uses `libsodium-wrappers` for GitHub secret encryption
- Reads from `workspaces/secrets/secrets/` (same as Terraform)

**2. Workflow**: `.github/workflows/sync-enterprise-secrets.yml`
- Triggered on push to secrets dir or manual dispatch
- Uses same AWS auth pattern as generator/secrets jobs
- Builds action at runtime

### To Test
```bash
# Trigger the sync workflow with dry-run first
gh workflow run sync-enterprise-secrets \
  --repo /terraform-organization-administration \
  -f dry_run=true

# Then run for real
gh workflow run sync-enterprise-secrets \
  --repo /terraform-organization-administration \
  -f dry_run=false
```

### Why This Works
1. **Reads from source** - SOPS files are the source of truth, no visibility restrictions
2. **Same auth pattern** - Uses `EXTERNAL_CI_ACCESS_KEY`/`SECRET_KEY` that's already working
3. **Proper encryption** - Uses libsodium sealed box for GitHub secret format
4. **All secrets sync** - Including SSH keys, because we read from files, not GitHub secrets

Shall I trigger a test run of this workflow?

## Delegation Inputs
- BRANCH_fix_vendor-connectors-pypi-name_task.md: 🔍 Forensic Recovery: Branch fix/vendor-connectors-pypi-name
- SYNTHESIS_task.md: 📊 Forensic Recovery: Synthesis & Consolidation
