# Active Context - jbcom Control Center

## Current Status: SECRET STANDARDIZATION & CI FIX COMPLETE

Standardized secret naming across the codebase and fixed CI failures caused by broken token fallbacks.

### What Was Fixed/Added
1. ✅ **CI Resilience**: Updated all workflows to prefer `JULES_GITHUB_TOKEN` and use robust fallbacks to `CI_GITHUB_TOKEN` and `GITHUB_TOKEN`.
2. ✅ **Security Hardening**: Removed hardcoded GitHub PATs from `memory-bank/activeContext.md` and `docs/OSS-REPO-SYNC-CLEANUP.md`.
3. ✅ **Secret Sync Update**: `scripts/sync-secrets` now includes all required secrets for the curator workflow.
4. ✅ **Naming Standardization**: Unified `GOOGLE_JULES_API_KEY`, `CURSOR_API_KEY`, and `JULES_GITHUB_TOKEN` across docs and scripts.
5. ✅ **Orchestrator Fallback**: Enhanced `scripts/cursor-jules-orchestrator.mjs` (root and always-sync) to support both `GOOGLE_JULES_API_KEY` and the older `JULES_API_KEY`.

### Manual Actions Required
The following secrets MUST be added to the repository by an administrator (agent lacks `gh secret set` permissions):
- `JULES_GITHUB_TOKEN`: (Obtain from GitHub settings - PAT with repo access)
- `OLLAMA_API_URL`: `https://ollama.com/api`
- `CURSOR_API_KEY`: (Obtain from Cursor team/dashboard)
- `GOOGLE_JULES_API_KEY`: (Obtain from Google AI Studio)

### For Next Agent
- Verify all secrets are added to the repo.
- Run `./scripts/sync-secrets --all` to propagate secrets to managed repositories.
- Trigger `Ecosystem Curator` workflow manually to verify.
