# Messages 281-287

## [281] 🤖 ASSISTANT

Now I understand the pattern. Let me create a proper JavaScript GitHub Action that:
1. Authenticates with AWS (same pattern as generator/secrets jobs)
2. Decrypts SOPS files using AWS KMS
3. Syncs to all enterprise orgs

---

## [282] 🤖 ASSISTANT

Now let me create the workflow that uses this action:

---

## [283] 🤖 ASSISTANT

Let me install dependencies and build the action:

---

## [284] 🤖 ASSISTANT

Let me use a proper libsodium library for the encryption:

---

## [285] 🤖 ASSISTANT

The action is built. Let me add everything to git and commit:

---

## [286] 🤖 ASSISTANT

The workflow builds the action at runtime, so we don't need the dist folder committed. Let me commit what we have:

---

## [287] 🤖 ASSISTANT

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
│  - fsc-internal-tooling-administration │
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
  --repo fsc-internal-tooling-administration/terraform-organization-administration \
  -f dry_run=true

# Then run for real
gh workflow run sync-enterprise-secrets \
  --repo fsc-internal-tooling-administration/terraform-organization-administration \
  -f dry_run=false
```

### Why This Works
1. **Reads from source** - SOPS files are the source of truth, no visibility restrictions
2. **Same auth pattern** - Uses `EXTERNAL_CI_ACCESS_KEY`/`SECRET_KEY` that's already working
3. **Proper encryption** - Uses libsodium sealed box for GitHub secret format
4. **All secrets sync** - Including SSH keys, because we read from files, not GitHub secrets

Shall I trigger a test run of this workflow?

---

