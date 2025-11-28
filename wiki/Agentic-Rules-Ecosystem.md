# Ecosystem Repositories

This control center manages the jbcom Python library ecosystem via **MONOREPO ARCHITECTURE**.

---

## 🏗️ ARCHITECTURE: All Code Lives Here

**ALL Python ecosystem code is in `packages/` in this repository.**

```
jbcom-control-center/packages/
├── extended-data-types/    → syncs to → jbcom/extended-data-types → PyPI
├── lifecyclelogging/       → syncs to → jbcom/lifecyclelogging → PyPI
├── directed-inputs-class/  → syncs to → jbcom/directed-inputs-class → PyPI
└── vendor-connectors/      → syncs to → jbcom/vendor-connectors → PyPI
```

### Workflow
1. **Edit** code in `packages/`
2. **PR** to control-center main
3. **Sync workflow** creates PRs in public repos
4. **Merge** public PRs → CI → PyPI release

### Why Monorepo
- ✅ No cloning external repos
- ✅ No GitHub API gymnastics
- ✅ Single source of truth
- ✅ Cross-package changes in ONE PR
- ✅ Dependencies always aligned

---

## 📦 Package Details

### 1. extended-data-types (FOUNDATION)
**Location:** `packages/extended-data-types/`
**PyPI:** `extended-data-types`
**Public Repo:** `jbcom/extended-data-types`

The foundation library - ALL other packages depend on this.

**Provides:**
- Re-exported libraries: `gitpython`, `inflection`, `lark`, `orjson`, `python-hcl2`, `ruamel.yaml`, `sortedcontainers`, `wrapt`
- Utilities: `strtobool`, `strtopath`, `make_raw_data_export_safe`, `get_unique_signature`
- Serialization: `decode_yaml`, `encode_yaml`, `decode_json`, `encode_json`
- Collections: `flatten_map`, `filter_map`, and more

**Rule:** Before adding ANY dependency to other packages, check if extended-data-types provides it.

### 2. lifecyclelogging
**Location:** `packages/lifecyclelogging/`
**PyPI:** `lifecyclelogging`
**Public Repo:** `jbcom/lifecyclelogging`

Structured lifecycle logging with automatic sanitization.

**Depends on:** extended-data-types

### 3. directed-inputs-class
**Location:** `packages/directed-inputs-class/`
**PyPI:** `directed-inputs-class`
**Public Repo:** `jbcom/directed-inputs-class`

Declarative input validation and processing.

**Depends on:** extended-data-types

### 4. vendor-connectors
**Location:** `packages/vendor-connectors/`
**PyPI:** `vendor-connectors`
**Public Repo:** `jbcom/vendor-connectors`

Unified vendor connectors (AWS, GCP, GitHub, Slack, Vault, Zoom).

**Depends on:** extended-data-types, lifecyclelogging, directed-inputs-class

---

## 🔗 Dependency Chain

```
extended-data-types (FOUNDATION)
├── lifecyclelogging
├── directed-inputs-class
└── vendor-connectors (depends on BOTH)
```

**Release Order:** Always release in this order:
1. extended-data-types
2. lifecyclelogging
3. directed-inputs-class
4. vendor-connectors

---

## 🔧 Working With Packages

### Edit Code
```bash
# Just edit files directly!
vim packages/extended-data-types/src/extended_data_types/type_utils.py
vim packages/vendor-connectors/pyproject.toml
```

### Run Tests
```bash
cd packages/extended-data-types && pip install -e ".[tests]" && pytest
cd packages/lifecyclelogging && pip install -e ".[tests]" && pytest
```

### Align Dependencies
```bash
# Update version across all packages
sed -i 's/extended-data-types>=.*/extended-data-types>=2025.11.200/' \
  packages/*/pyproject.toml
```

### Create PR
```bash
git checkout -b fix/whatever
git add -A && git commit -m "Fix: description"
git push -u origin fix/whatever
gh pr create --title "Fix: whatever"
```

---

## 🔄 Sync Configuration

### Files
- `packages/ECOSYSTEM.toml` - Source of truth
- `.github/sync.yml` - What syncs where
- `.github/workflows/sync-packages.yml` - Sync workflow

### Triggers
- Push to main with `packages/**` changes
- Manual workflow dispatch
- Release published

### Secret
`CI_GITHUB_TOKEN` from Doppler - has write access to all jbcom repos

---

## ⚠️ Rules

### DO
- ✅ Edit code in `packages/` directly
- ✅ Use regular git for this repo
- ✅ Check `packages/ECOSYSTEM.toml` for relationships
- ✅ Use extended-data-types utilities
- ✅ Release in dependency order

### DON'T
- ❌ Clone external repos - code is HERE
- ❌ Add duplicate utilities
- ❌ Skip the sync workflow
- ❌ Push directly to main (use PRs)

---

## 🎯 Eliminate Duplication

### Check Before Adding Dependencies
Always check `packages/extended-data-types/pyproject.toml` first.

### Red Flags
- `utils.py` > 100 lines → duplicating extended-data-types
- Direct `import inflection` → should use extended-data-types
- Custom JSON/YAML functions → use `encode_json`, `decode_yaml`

### Correct Pattern
```python
# ✅ Use foundation library
from extended_data_types import strtobool, make_raw_data_export_safe

# ❌ Don't reimplement
def my_str_to_bool(val):
    return val.lower() in ("true", "yes", "1")
```

---

## 📊 Health Checks

### Check Public Repo CI
```bash
for repo in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  gh run list --repo jbcom/$repo --limit 3
done
```

### Check PyPI Versions
```bash
pip index versions extended-data-types
pip index versions lifecyclelogging
pip index versions vendor-connectors
```

### Trigger Manual Sync
```bash
gh workflow run "Sync Packages to Public Repos" --repo jbcom/jbcom-control-center
```

---

**Source of Truth:** `packages/ECOSYSTEM.toml`
**All code is in:** `packages/`
**Sync handles:** Pushing to public repos and PyPI
