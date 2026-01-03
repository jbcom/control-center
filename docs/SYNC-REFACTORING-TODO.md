# Ecosystem Sync Refactoring - In Progress

## Status: Phase 1 Complete - sync-files/ Structure Created

### ✅ Completed
- Created consolidated `sync-files/` directory structure
- Merged `repository-files/` and `global-sync/` content
- Organized by always-sync vs initial-only
- Organized by language (global, python, nodejs, go, terraform, rust)

### 🚧 In Progress  
- Updating `ecosystem-sync.yml` to use new structure
- Adding Phase 0 cleanup for org control-centers
- Removing cascade phases (1c, 2, 3)
- Implementing direct sync logic

### 📋 Next Steps

1. **Update ecosystem-sync.yml**:
   - Replace `global-sync/` references with `sync-files/always-sync/global/`
   - Replace `repository-files/` references with `sync-files/always-sync/`
   - Add language detection logic for repos
   - Remove org control-center cascade (phases 1c, 2, 3)

2. **Add Phase 0 cleanup**:
   ```yaml
   - name: Archive old org control-centers
     run: |
       for org in arcade-cabinet agentic-dev-library extended-data-library strata-game-library; do
         if gh repo view "$org/control-center" >/dev/null 2>&1; then
           gh repo archive "$org/control-center" --yes
         fi
       done
   ```

3. **Implement direct sync with language detection**:
   ```bash
   # Detect language
   if [ -f "package.json" ]; then LANG="nodejs"
   elif [ -f "go.mod" ]; then LANG="go"
   elif [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then LANG="python"
   elif [ -f "Cargo.toml" ]; then LANG="rust"
   elif [ -f "main.tf" ]; then LANG="terraform"
   else LANG="global"
   fi
   
   # Sync always-sync files
   cp -r sync-files/always-sync/global/. .
   cp -r sync-files/always-sync/$LANG/. .
   
   # Sync initial-only (first time)
   if [ ! -f ".github/.ecosystem-synced" ]; then
     cp -r sync-files/initial-only/global/. .
     touch .github/.ecosystem-synced
   fi
   ```

### Expected Outcome
- Workflow reduced from 590 lines to ~300 lines
- Direct sync eliminates org control-center complexity
- Clearer, more maintainable architecture
