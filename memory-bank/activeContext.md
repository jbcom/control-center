# Active Context - jbcom Control Center

## Current Status: CI FIXES AND SECRET STANDARDIZATION COMPLETE

Standardized secret naming across the codebase and fixed systemic CI failures in the Ollama PR Orchestrator.

### What Was Fixed/Added
1. ✅ **CI Auth Fixed**: Updated all workflows to use `github.token` instead of `secrets.GITHUB_TOKEN`, resolving git authentication errors in draft PRs and bot-triggered runs.
2. ✅ **Permissions Hardening**: Added `contents: write` permissions to jobs performing automated commits (e.g., in `ollama-cloud-pr-review.yml`).
3. ✅ **Secret Standardization Usage**: Updated `ollama-cloud-pr-review.yml` to utilize the new `OLLAMA_API_URL` secret.
4. ✅ **Template Synchronization**: Propagated all CI and secret fixes to the templates in `repository-files/always-sync/` to ensure managed repositories receive the improved workflows.
5. ✅ **Doc Update**: Comprehensive update to `CLAUDE.md` documentation for all tokens and API keys.

### Manual Actions Required
The following secrets still MUST be added to the repository by an administrator (if not already done):
- `JULES_GITHUB_TOKEN`: `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`
- `OLLAMA_API_URL`: `https://ollama.com/api`
- `CURSOR_API_KEY`: (Obtain from Cursor team/dashboard)
- `GOOGLE_JULES_API_KEY`: (Obtain from Google AI Studio)

### For Next Agent
- Verify CI passes green on PR #456.
- Run `./scripts/sync-secrets --all` once secrets are added to propagate them.
- Monitor `Ollama PR Orchestrator` for successful automated feedback resolution.
