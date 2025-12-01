# Unified Control Center Ecosystem

This control center manages **TWO ecosystems** from a single repository:

| Ecosystem | Path | Output |
|-----------|------|--------|
| **jbcom** | `packages/` | PyPI + npm |
| **FlipsideCrypto** | `ecosystems/flipside-crypto/` | AWS/GCP infrastructure |

---

## 🏗️ ARCHITECTURE

```
jbcom-control-center/
├── packages/                          # jbcom ecosystem
│   ├── extended-data-types/           # → PyPI
│   ├── lifecyclelogging/              # → PyPI
│   ├── directed-inputs-class/         # → PyPI
│   ├── python-terraform-bridge/       # → PyPI
│   ├── vendor-connectors/             # → PyPI
│   └── agentic-control/               # → npm
│
├── ecosystems/flipside-crypto/        # FlipsideCrypto ecosystem
│   ├── terraform/
│   │   ├── modules/                   # 100+ reusable modules
│   │   └── workspaces/                # 44 live workspaces
│   ├── sam/                           # AWS Lambda apps
│   ├── lib/                           # Python libraries
│   └── config/                        # State paths, pipelines
│
└── ECOSYSTEM.toml                     # Unified manifest
```

---

## 📦 jbcom Packages

### Python (PyPI)

| Package | Description | Public Repo |
|---------|-------------|-------------|
| extended-data-types | Foundation utilities | jbcom/extended-data-types |
| lifecyclelogging | Structured logging | jbcom/lifecyclelogging |
| directed-inputs-class | Input validation | jbcom/directed-inputs-class |
| python-terraform-bridge | Terraform utils | jbcom/python-terraform-bridge |
| vendor-connectors | Cloud SDKs | jbcom/vendor-connectors |

### Node.js (npm)

| Package | Description | Public Repo |
|---------|-------------|-------------|
| agentic-control | Agent orchestration | jbcom/agentic-control |

### Dependency Chain

```
extended-data-types (foundation)
├── lifecyclelogging
├── directed-inputs-class
├── python-terraform-bridge
└── vendor-connectors (depends on all above)

agentic-control (independent Node.js package)
```

---

## 🏢 FlipsideCrypto Infrastructure

### Terraform Modules (100+)

| Category | Path | Count |
|----------|------|-------|
| AWS | `terraform/modules/aws/` | 70+ |
| Google | `terraform/modules/google/` | 38 |
| GitHub | `terraform/modules/github/` | 10+ |
| Terraform | `terraform/modules/terraform/` | 5 |

### Terraform Workspaces (44)

| Organization | Path | Count |
|--------------|------|-------|
| AWS | `terraform/workspaces/terraform-aws-organization/` | 37 |
| Google | `terraform/workspaces/terraform-google-organization/` | 7 |

### SAM Applications

| App | Purpose |
|-----|---------|
| secrets-config | Secrets configuration |
| secrets-merging | Secrets merging |
| secrets-syncing | Secrets syncing |

---

## 🔑 Token Configuration

```json
{
  "tokens": {
    "organizations": {
      "jbcom": { "tokenEnvVar": "GITHUB_JBCOM_TOKEN" },
      "FlipsideCrypto": { "tokenEnvVar": "GITHUB_FSC_TOKEN" }
    },
    "prReviewTokenEnvVar": "GITHUB_JBCOM_TOKEN"
  }
}
```

**Token switching is automatic** via `agentic-control`.

---

## 🔄 Release Flow

### Python Packages
```
Conventional commit → PSR version bump → PyPI publish → Public repo sync
```

### Node.js Package
```
Conventional commit → CI version bump → npm publish → Public repo sync
```

### Terraform
```
Edit → Plan → Apply (manual with appropriate credentials)
```

---

## 🔧 Working With Each Ecosystem

### jbcom Packages

```bash
# Edit
vim packages/extended-data-types/src/extended_data_types/utils.py

# Test
tox -e extended-data-types

# PR
git checkout -b fix/something
git commit -m "fix(edt): description"
git push -u origin fix/something
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create
```

### FlipsideCrypto Infrastructure

```bash
# Navigate
cd ecosystems/flipside-crypto/terraform/workspaces/terraform-aws-organization/security

# Plan
terraform plan

# Apply (requires AWS credentials)
terraform apply
```

### agentic-control

```bash
# Build
cd packages/agentic-control && pnpm build

# Test
pnpm test

# Use CLI
agentic fleet list
agentic triage analyze <session>
```

---

## ⚠️ Rules

### DO
- ✅ Use `agentic-control` for cross-ecosystem operations
- ✅ Let token switching happen automatically
- ✅ Check `ECOSYSTEM.toml` for relationships
- ✅ Use conventional commits with scopes

### DON'T
- ❌ Hardcode tokens
- ❌ Mix ecosystem concerns in single commits
- ❌ Push directly to main
- ❌ Modify Terraform state manually

---

## 📊 Health Checks

```bash
# Check Python packages
for pkg in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/$pkg --limit 1
done

# Check agentic-control
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/agentic-control --limit 1

# Check agent fleet
agentic fleet list --running
```

---

**Manifest:** `ECOSYSTEM.toml`
**Agent Config:** `agentic.config.json`
**Token Docs:** `docs/TOKEN-MANAGEMENT.md`
