# Evaluation: Shift to Public OSS Ecosystem Repository

> **Status**: PROPOSAL EVALUATION  
> **Date**: 2025-12-02  
> **Author**: Agent bc-cf56 (Cursor Background Agent)

## Executive Summary

This document evaluates shifting from the current **private monorepo with sync to public repos** model to a **public OSS monorepo controlled by private control center** model. This would leverage GitHub's free security tooling (CodeQL), eliminate the sync mechanism complexity, consolidate 7 public repos into one, and dogfood the `agentic-control` package.

### Recommendation: ✅ PROCEED WITH EVALUATION PILOT

The benefits strongly outweigh the challenges. A phased migration approach is recommended.

---

## Table of Contents

1. [Current Architecture](#current-architecture)
2. [Proposed Architecture](#proposed-architecture)
3. [Benefits Analysis](#benefits-analysis)
4. [Challenges & Mitigations](#challenges--mitigations)
5. [What Stays Private vs Public](#what-stays-private-vs-public)
6. [Naming Options](#naming-options)
7. [Migration Path](#migration-path)
8. [Technical Implementation](#technical-implementation)
9. [Risk Assessment](#risk-assessment)
10. [Recommendation](#recommendation)

---

## Current Architecture

### Repository Structure

```
PRIVATE: jbcom/jbcom-control-center
├── packages/                         # All package source code
│   ├── extended-data-types/          # → synced to jbcom/extended-data-types
│   ├── lifecyclelogging/             # → synced to jbcom/lifecyclelogging
│   ├── directed-inputs-class/        # → synced to jbcom/directed-inputs-class
│   ├── python-terraform-bridge/      # → synced to jbcom/python-terraform-bridge
│   ├── vendor-connectors/            # → synced to jbcom/vendor-connectors
│   ├── agentic-control/              # → synced to jbcom/agentic-control
│   └── vault-secret-sync/            # → synced to jbcom/vault-secret-sync
├── ecosystems/flipside-crypto/       # FSC infrastructure (stays private)
├── memory-bank/                      # Agent context
├── .github/sync/                     # Sync configs per package
└── agentic.config.json              # Agent token management

PUBLIC: jbcom/extended-data-types     (empty except synced code)
PUBLIC: jbcom/lifecyclelogging        (empty except synced code)
PUBLIC: jbcom/directed-inputs-class   (empty except synced code)
PUBLIC: jbcom/python-terraform-bridge (empty except synced code)
PUBLIC: jbcom/vendor-connectors       (empty except synced code)
PUBLIC: jbcom/agentic-control         (empty except synced code)
PUBLIC: jbcom/vault-secret-sync       (fork with enhancements)
```

### Release Flow (Current)

```
Developer commits to private monorepo
         ↓
CI runs in private repo (tests, lint, build)
         ↓
PSR bumps version, creates tag
         ↓
Publishes to PyPI/npm
         ↓
BetaHuhn/repo-file-sync-action syncs to 7 public repos
         ↓
Users see code in public repos
```

### Pain Points

| Issue | Impact |
|-------|--------|
| **7 separate repos** | Maintenance overhead, inconsistent issues/PRs |
| **Sync complexity** | Extra CI step, config files, potential failures |
| **No CodeQL** | Private repos don't get free advanced security |
| **Paid Actions minutes** | Private repo CI costs money |
| **Fragmented community** | Issues/PRs split across repos |
| **Redundant releases** | Each public repo gets synced release commits |

---

## Proposed Architecture

### Repository Structure

```
PRIVATE: jbcom/jbcom-control-center (RENAMED: jbcom-control)
├── ecosystems/
│   ├── flipside-crypto/              # FSC infrastructure (stays here)
│   └── jbcom/                        # NEW: Pointer to public ecosystem
│       ├── packages -> (symlink/submodule to public repo)
│       └── memory-bank/
├── memory-bank/                      # Control center context
├── agentic.config.json              # Manages ALL ecosystems including public
└── .ruler/                          # Agent rules for controlling ecosystems

PUBLIC: jbcom/jbcom-ecosystem (NEW - THE PUBLIC MONOREPO)
├── packages/
│   ├── extended-data-types/
│   ├── lifecyclelogging/
│   ├── directed-inputs-class/
│   ├── python-terraform-bridge/
│   ├── vendor-connectors/
│   ├── agentic-control/
│   └── vault-secret-sync/
├── .github/workflows/ci.yml          # Full CI/CD
├── pyproject.toml                   # UV workspace
├── package.json                     # PNPM workspace
├── ECOSYSTEM.toml                   # Package manifest
└── memory-bank/                     # Agent context (for public contributions)

ARCHIVED/DEPRECATED:
- jbcom/extended-data-types          (redirect to jbcom-ecosystem)
- jbcom/lifecyclelogging             (redirect to jbcom-ecosystem)
- jbcom/directed-inputs-class        (redirect to jbcom-ecosystem)
- jbcom/python-terraform-bridge      (redirect to jbcom-ecosystem)
- jbcom/vendor-connectors            (redirect to jbcom-ecosystem)
- jbcom/agentic-control              (redirect to jbcom-ecosystem)
- jbcom/vault-secret-sync            (redirect to jbcom-ecosystem)
```

### Release Flow (Proposed)

```
Developer commits to PUBLIC jbcom/jbcom-ecosystem
         ↓
GitHub free CI runs (tests, lint, build)
         ↓
CodeQL scans (FREE for public repos)
         ↓
PSR bumps version, creates tag
         ↓
Publishes to PyPI/npm
         ↓
DONE - No sync needed!

PRIVATE control center:
- Monitors public repo via agentic-control
- Spawns agents to make contributions
- Manages secrets via environment variables in public repo settings
```

---

## Benefits Analysis

### 1. Free GitHub Advanced Security (CodeQL)

| Feature | Private Repo | Public Repo |
|---------|-------------|-------------|
| **CodeQL code scanning** | ❌ Paid ($49/user/month GHAS) | ✅ FREE |
| **Secret scanning** | ❌ Paid | ✅ FREE |
| **Dependency review** | ❌ Paid | ✅ FREE |
| **Security advisories** | ⚠️ Limited | ✅ Full |
| **SBOM generation** | ⚠️ Manual | ✅ Automatic |

**Value**: CodeQL finds real vulnerabilities. For 5 Python packages + 1 Node.js + 1 Go package, this is significant.

### 2. Free GitHub Actions Minutes

| Plan | Private | Public |
|------|---------|--------|
| **Minutes/month** | 2,000 (Free) / 3,000 (Pro) | **UNLIMITED** |
| **Cost at scale** | ~$0.008/min Linux | FREE |

Current CI runs ~10 min per push × 50 pushes/month = 500 minutes. At scale, this saves ~$4/month but more importantly removes minute limits during active development.

### 3. Simplified Architecture

| Metric | Current | Proposed |
|--------|---------|----------|
| **Repos to manage** | 8 (1 private + 7 public) | 2 (1 private + 1 public) |
| **Sync configs** | 7 YAML files | 0 |
| **CI workflows** | 2 (private + sync) | 1 (public) |
| **Issue trackers** | 8 (fragmented) | 2 (focused) |
| **Release coordination** | Complex sync | Direct |

### 4. Dogfooding `agentic-control`

The private control center would use `agentic-control` to:
- Monitor the public repo (like it monitors FlipsideCrypto)
- Spawn agents for contributions
- Manage PRs and releases
- Coordinate cross-ecosystem changes

```json
// agentic.config.json (updated)
{
  "tokens": {
    "organizations": {
      "jbcom": {
        "tokenEnvVar": "GITHUB_JBCOM_TOKEN"
      }
    }
  },
  "ecosystems": {
    "jbcom-ecosystem": {
      "repository": "jbcom/jbcom-ecosystem",
      "type": "packages",
      "visibility": "public"
    },
    "flipside-crypto": {
      "path": "ecosystems/flipside-crypto",
      "type": "infrastructure",
      "visibility": "private"
    }
  }
}
```

### 5. Community Benefits

| Feature | Current (7 repos) | Proposed (1 repo) |
|---------|------------------|-------------------|
| **Star count** | Split across repos | Consolidated |
| **Contributor PRs** | Scattered | Single location |
| **Issue tracking** | Fragmented | Unified |
| **Discussions** | 7 separate | 1 unified |
| **Dependabot** | 7 configs | 1 config |

### 6. PyPI/npm Subpath Installation

Users can already install packages independently. With a monorepo, documentation becomes clearer:

```bash
# Install individual packages (no change)
pip install extended-data-types
pip install vendor-connectors

# Clone the monorepo for development
git clone https://github.com/jbcom/jbcom-ecosystem.git
cd jbcom-ecosystem
uv sync  # Install all packages
```

---

## Challenges & Mitigations

### Challenge 1: Secrets Management

**Problem**: Public repo CI needs secrets (PYPI_TOKEN, NPM_TOKEN, etc.)

**Mitigation**: 
- Use GitHub Environments with protection rules
- Secrets only available on `main` branch pushes
- All secrets visible in public repo settings (names, not values)

```yaml
# .github/workflows/release.yml
jobs:
  release:
    if: github.ref == 'refs/heads/main'
    environment: production  # Protected environment
    steps:
      - uses: pypa/gh-action-pypi-publish@v1
        with:
          password: ${{ secrets.PYPI_TOKEN }}
```

### Challenge 2: Git History

**Problem**: Moving to public repo loses private repo history

**Mitigation Options**:

| Option | Description | Preserves History |
|--------|-------------|-------------------|
| A. Fresh start | New repo, archive old | ❌ No |
| B. Subtree split | Extract packages/ to new repo | ✅ Partial |
| C. Full migration | Make entire repo public, move private stuff | ✅ Full |

**Recommended**: Option B - preserves package history while keeping private stuff private.

```bash
# Extract packages/ with full history
git subtree split -P packages -b packages-only
# Push to new public repo
git push jbcom-ecosystem packages-only:main
```

### Challenge 3: Private Control Center Coordination

**Problem**: How does private center control public repo?

**Mitigation**: Same pattern as FlipsideCrypto:

```bash
# Private control center spawns agents to public repo
agentic fleet spawn "https://github.com/jbcom/jbcom-ecosystem" "Fix CI" --ref main

# Or directly make changes
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --repo jbcom/jbcom-ecosystem \
  --title "fix(edt): resolve issue" \
  --body "From control center"
```

### Challenge 4: FlipsideCrypto Stays Private

**Problem**: FSC infrastructure cannot be public

**Mitigation**: FSC stays in private control center. Only jbcom packages move.

```
PRIVATE control-center:
├── ecosystems/flipside-crypto/  # STAYS HERE
└── config/                      # Token management, agent rules

PUBLIC jbcom-ecosystem:
├── packages/                    # MOVES HERE
└── docs/                        # MOVES HERE
```

### Challenge 5: Breaking Existing Users

**Problem**: Users pointing to old public repos

**Mitigation**: 
1. Archive old repos (not delete)
2. Update README in each to point to monorepo
3. PyPI package names stay the same
4. No breaking changes for pip/npm users

```markdown
# In jbcom/extended-data-types README
> ⚠️ This repository is archived. Development has moved to:
> [jbcom/jbcom-ecosystem](https://github.com/jbcom/jbcom-ecosystem)
```

---

## What Stays Private vs Public

### Stays in PRIVATE jbcom-control-center

| Item | Reason |
|------|--------|
| `ecosystems/flipside-crypto/` | Contains infrastructure secrets, internal configs |
| `memory-bank/` (FSC section) | Internal planning context |
| Agent orchestration rules | Security-sensitive coordination |
| Token configurations | `agentic.config.json` with token envvar names |
| Internal tooling scripts | Not relevant to OSS |

### Moves to PUBLIC jbcom-ecosystem

| Item | Reason |
|------|--------|
| `packages/` | All package source code |
| `pyproject.toml` | UV workspace config |
| `package.json` | PNPM workspace config |
| `ECOSYSTEM.toml` | Package manifest |
| `.github/workflows/` | CI/CD (adapted for public) |
| `docs/` | Package documentation |
| `templates/` | Library templates |
| `memory-bank/` (public section) | OSS contribution context |
| `AGENTS.md`, `.cursorrules` | AI agent instructions |

---

## Naming Options

### For the Public Ecosystem Repository

| Option | Name | Pros | Cons |
|--------|------|------|------|
| **A** | `jbcom-ecosystem` | Clear, matches ECOSYSTEM.toml | Generic |
| **B** | `jbcom-packages` | Descriptive | Limits future expansion |
| **C** | `jbcom-oss` | Clear OSS focus | Redundant (all public is OSS) |
| **D** | `jbcom-libraries` | Technical | Includes Go tool, not just libs |
| **E** | `jbcom-sdk` | Professional | Implies SDK, which this is! |
| **F** | `jbcom-toolkit` | Friendly | Vague |

**Recommended**: `jbcom-ecosystem` or `jbcom-sdk`

- `jbcom-ecosystem` emphasizes the unified nature
- `jbcom-sdk` emphasizes it's tooling for building things

### For the Private Control Center

| Option | Name | Pros | Cons |
|--------|------|------|------|
| Keep as `jbcom-control-center` | Continuity | Longer |
| Rename to `jbcom-control` | Shorter | Breaking bookmarks |
| Rename to `jbcom-operations` | Descriptive | Less clear |

**Recommended**: Keep as `jbcom-control-center` to avoid confusion.

---

## Migration Path

### Phase 1: Preparation (Week 1)

1. **Create public repo structure**
   ```bash
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh repo create jbcom/jbcom-ecosystem \
     --public \
     --description "Unified SDK: Python/TypeScript packages for infrastructure automation"
   ```

2. **Set up secrets in public repo**
   - PYPI_TOKEN
   - NPM_TOKEN  
   - CI_GITHUB_TOKEN (for creating releases)

3. **Configure CodeQL**
   ```yaml
   # .github/workflows/codeql.yml
   name: CodeQL
   on: [push, pull_request, schedule]
   jobs:
     analyze:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           language: [python, javascript, go]
       steps:
         - uses: github/codeql-action/init@v3
         - uses: github/codeql-action/analyze@v3
   ```

### Phase 2: Code Migration (Week 2)

1. **Extract packages with history**
   ```bash
   cd jbcom-control-center
   git subtree split -P packages -b packages-export
   
   cd ../jbcom-ecosystem
   git pull ../jbcom-control-center packages-export
   ```

2. **Adapt CI/CD**
   - Copy and modify `.github/workflows/ci.yml`
   - Update paths (remove `packages/` prefix)
   - Keep PSR configuration

3. **Test full pipeline**
   - Create test PR
   - Verify tests pass
   - Verify PSR version detection works
   - Verify PyPI publish (test.pypi.org first)

### Phase 3: Cutover (Week 3)

1. **Freeze private repo packages/**
   - Stop accepting package changes
   - All changes go to public repo

2. **Update control center**
   - Remove `packages/` directory
   - Update agentic.config.json with ecosystem reference
   - Update memory-bank with new structure

3. **Archive old public repos**
   - Add redirect READMEs
   - Archive (read-only) each repo

### Phase 4: Validation (Week 4)

1. **Monitor public repo**
   - Verify CodeQL is running
   - Verify releases work
   - Check community can create issues/PRs

2. **Test control center coordination**
   - Spawn agent to public repo
   - Create PR from control center
   - Verify token management works

---

## Technical Implementation

### Updated agentic.config.json

```json
{
  "$schema": "https://agentic-control.dev/schema/config.json",
  "tokens": {
    "organizations": {
      "jbcom": {
        "name": "jbcom",
        "tokenEnvVar": "GITHUB_JBCOM_TOKEN",
        "defaultBranch": "main"
      },
      "FlipsideCrypto": {
        "name": "FlipsideCrypto", 
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      }
    }
  },
  "ecosystems": {
    "jbcom-packages": {
      "repository": "jbcom/jbcom-ecosystem",
      "type": "packages",
      "visibility": "public",
      "packages": [
        "extended-data-types",
        "lifecyclelogging",
        "directed-inputs-class",
        "python-terraform-bridge",
        "vendor-connectors",
        "agentic-control",
        "vault-secret-sync"
      ]
    },
    "flipside-crypto": {
      "path": "ecosystems/flipside-crypto",
      "type": "infrastructure",
      "visibility": "private"
    }
  },
  "defaultModel": "claude-sonnet-4-5-20250929"
}
```

### Updated ECOSYSTEM.toml (in public repo)

```toml
[ecosystem]
name = "jbcom-ecosystem"
description = "Unified SDK for infrastructure automation"
version = "1.0.0"

[packages.extended-data-types]
type = "python"
path = "packages/extended-data-types"
pypi = "extended-data-types"

[packages.lifecyclelogging]
type = "python"
path = "packages/lifecyclelogging"
pypi = "lifecyclelogging"
depends_on = ["extended-data-types"]

[packages.agentic-control]
type = "nodejs"
path = "packages/agentic-control"
npm = "agentic-control"

[packages.vault-secret-sync]
type = "go"
path = "packages/vault-secret-sync"
docker = "docker.io/jbcom/vault-secret-sync"
helm = "oci://docker.io/jbcom/vault-secret-sync"
```

### New Control Center Structure

```
jbcom-control-center/
├── ecosystems/
│   ├── flipside-crypto/           # KEPT - private infrastructure
│   │   ├── terraform/
│   │   ├── sam/
│   │   ├── lib/
│   │   └── memory-bank/
│   └── jbcom/                     # NEW - reference to public repo
│       └── README.md              # Points to jbcom-ecosystem
├── memory-bank/
│   ├── activeContext.md
│   └── progress.md
├── agentic.config.json            # Updated with ecosystems
├── .ruler/                        # Agent rules
└── docs/
    └── ECOSYSTEM-MANAGEMENT.md   # How to manage both ecosystems
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Secret leak in public repo | Low | High | Use GitHub Environments, audit access |
| Migration breaks releases | Medium | High | Test on test.pypi.org first |
| Community confusion | Medium | Medium | Clear redirect READMEs, announcement |
| Loss of git history | Low | Medium | Use subtree split to preserve |
| CodeQL false positives | Medium | Low | Configure appropriately |
| Control center coordination fails | Low | Medium | Test agentic-control extensively |

---

## Recommendation

### ✅ PROCEED WITH PILOT

**Reasons:**

1. **Strong benefits**: Free CodeQL, free Actions, simplified architecture
2. **Proven pattern**: FSC ecosystem management already works
3. **Dogfooding opportunity**: Real test of agentic-control
4. **Community benefits**: Unified issue tracking, easier contributions
5. **No breaking changes**: PyPI package names unchanged

### Suggested Timeline

| Week | Milestone |
|------|-----------|
| 1 | Create `jbcom/jbcom-ecosystem`, set up secrets & CodeQL |
| 2 | Migrate packages with history, adapt CI |
| 3 | Cutover: freeze private packages, archive old repos |
| 4 | Validation and monitoring |

### Success Criteria

- [ ] CodeQL scanning operational on all languages
- [ ] At least one successful PyPI release from public repo
- [ ] At least one successful npm release from public repo
- [ ] Control center can spawn agents to public repo
- [ ] No regressions in package functionality
- [ ] Old repos archived with redirects

### Next Steps

1. **User approval** of this proposal
2. **Create pilot branch** in control center to test coordination
3. **Set up `jbcom/jbcom-ecosystem`** as empty repo
4. **Begin Phase 1** preparations

---

## Appendix: Commands Reference

### Create Public Repo
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh repo create jbcom/jbcom-ecosystem \
  --public \
  --description "Unified SDK: Python, TypeScript, Go packages for infrastructure automation" \
  --homepage "https://jbcom.github.io/jbcom-ecosystem"
```

### Enable CodeQL
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api \
  -X PUT /repos/jbcom/jbcom-ecosystem/vulnerability-alerts

GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api \
  -X PUT /repos/jbcom/jbcom-ecosystem/automated-security-fixes
```

### Extract Packages History
```bash
cd /path/to/jbcom-control-center
git subtree split -P packages -b packages-history

cd /path/to/jbcom-ecosystem
git remote add control-center /path/to/jbcom-control-center
git pull control-center packages-history --allow-unrelated-histories
```

### Archive Old Repo
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh repo archive jbcom/extended-data-types
```

---

*Document generated by Cursor Background Agent*  
*Branch: cursor/evaluate-shift-to-public-oss-ecosystem-repository-claude-4.5-opus-high-thinking-cf56*
