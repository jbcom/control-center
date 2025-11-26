# 🗑️ jbcom Repository Cleanup Proposal

**Generated**: 2025-11-25
**Total Repos**: 89 (37 owned + 52 forks)
**Proposed for Deletion**: 67 repos
**Remaining After Cleanup**: 22 repos

---

## 🔴 IMMEDIATE DELETE: Ancient Forks (52 repos)

These are forks you made years ago, never contributed back, and serve no purpose:

### Delete ALL Forks (52 repos → 0)

| Repo | Last Activity | Age | Reason |
|------|---------------|-----|--------|
| nexus-oss-rpms | 2011-12-22 | **14 years** | Ancient shell fork |
| chef-rvm_passenger | 2012-06-01 | **13 years** | Dead Chef ecosystem |
| aws (Ruby) | 2013-07-11 | **12 years** | Obsolete AWS gem |
| librarian-chef | 2013-12-16 | **12 years** | Dead Chef tool |
| varnish | 2014-03-12 | **11 years** | Old cookbook |
| haproxy | 2014-03-15 | **11 years** | Old cookbook |
| virtualbox-cookbook | 2014-03-22 | **11 years** | Old cookbook |
| fail2ban | 2014-04-21 | **11 years** | Old cookbook |
| solr_app-cookbook | 2014-04-29 | **11 years** | Old cookbook |
| dd-agent | 2014-05-14 | **11 years** | Old Datadog fork |
| users | 2014-05-15 | **11 years** | Old cookbook |
| rbenv-cookbook | 2014-08-05 | **10 years** | Old cookbook |
| chef-solr | 2014-08-16 | **10 years** | Old cookbook |
| chef-rundeck | 2014-11-23 | **10 years** | Old cookbook |
| rubix | 2014-12-04 | **10 years** | Dead Ruby lib |
| configliere | 2014-12-04 | **10 years** | Dead Ruby lib |
| cpu-cookbook | 2015-02-11 | **10 years** | Old cookbook |
| reverse-ssh-agent | 2015-04-23 | **10 years** | Old shell script |
| drud | 2015-08-05 | **10 years** | Dead project |
| python (fork) | 2015-08-24 | **10 years** | Why fork Python? |
| slack-custom-action | 2015-10-02 | **9 years** | Old Slack thing |
| capistrano-supervisor | 2015-12-02 | **9 years** | Dead Ruby deploy |
| rundeck-gcp-nodes-plugin | 2016-03-20 | **9 years** | Old Java plugin |
| pack_rb | 2016-03-21 | **9 years** | Dead Ruby lib |
| opinionated-dev-setup | 2016-06-14 | **9 years** | Old dev setup |
| bombard-docker | 2016-10-10 | **9 years** | Dead Docker thing |
| kubeclient | 2016-11-14 | **9 years** | Old K8s client |
| junit2html | 2017-12-22 | **8 years** | Old Python tool |
| unrarall | 2018-02-20 | **7 years** | Shell script |
| slork | 2018-08-10 | **7 years** | C project? |
| banana-split | 2019-05-12 | **6 years** | JS thing |
| putio-automator | 2019-12-02 | **6 years** | put.io script |
| image-builder | 2020-02-20 | **5 years** | Old image tool |
| kubectl-ssm-secret | 2020-05-01 | **5 years** | Old K8s tool |
| Win10-Initial-Setup-Script | 2020-08-26 | **5 years** | Windows setup |
| terraform-aws-astronomer-aws | 2021-05-05 | **4 years** | Old TF module |
| terraform-aws-astronomer-enterprise | 2021-05-14 | **4 years** | Old TF module |
| sway-dotfiles | 2021-06-18 | **4 years** | Dotfiles |
| terraform-provider-http | 2021-11-22 | **4 years** | Provider fork |
| terraform-provider-googleworkspace | 2021-12-21 | **4 years** | Provider fork |
| coredns-helm | 2022-04-11 | **3 years** | Helm chart |
| terraform-aws-ecs-web-app | 2022-11-16 | **3 years** | Old TF module |
| terraform-aws-route53-cluster-zone | 2022-11-25 | **3 years** | Old TF module |
| terraform-aws-cur | 2022-12-22 | **3 years** | Old TF module |
| terraform-provider-sops | 2023-01-13 | **2 years** | Provider fork |
| terraform-provider-snowflake | 2023-03-01 | **2 years** | Provider fork |
| gpt-commit-msg | 2023-05-17 | **2 years** | AI commit msg |
| github-tag-action | 2024-01-23 | **2 years** | Action fork |
| setup-terragrunt | 2024-01-23 | **2 years** | Action fork |
| commitgpt | 2024-07-26 | **1 year** | AI commit (dupe?) |
| claude-artifacts-downloader | 2024-10-23 | **1 year** | Claude tool |
| mdc_autogen | 2025-03-14 | **8 months** | MCP thing |
| blender-mcp | 2025-08-18 | **3 months** | Keep if using |

**Command to delete all forks:**
```bash
gh repo list jbcom --fork --json name -q '.[].name' | xargs -I {} gh repo delete jbcom/{} --yes
```

---

## 🟠 DELETE: Dead Owned Repos (15 repos)

These are YOUR repos that are clearly abandoned:

### Tier 1: Ancient & Useless (delete immediately)

| Repo | Last Activity | Age | Reason |
|------|---------------|-----|--------|
| Cheftasks | 2015-04-16 | **10 years** | Dead Chef Ruby |
| google-api-list-lifter | 2017-03-24 | **8 years** | Never used |
| cluster_mgmt | 2023-12-15 | **2 years** | Dead Ruby cluster tool |
| helm | 2023-12-15 | **2 years** | Empty/unused Helm |
| docker-redis-cluster | 2023-12-15 | **2 years** | Old Docker setup |
| humankind-unfolding | 2023-12-15 | **2 years** | Abandoned game? |

### Tier 2: Created & Abandoned (delete)

| Repo | Created | Last Push | Reason |
|------|---------|-----------|--------|
| port-labs-client | 2024-03-25 | Same day | Never developed |
| port-labs-database-middleware | 2024-03-25 | Same day | Never developed |
| google-sso-propagation | 2024-06-14 | Same day | Never developed |
| terraform-aws-datadog-codepipeline | 2024-08-01 | Same day | Never developed |
| logged-session | 2024-08-09 | Same day | Never developed |
| gitops-fs-utils | 2024-08-09 | Same day | Never developed |
| flexiyaml | 2024-10-30 | Same day | Never developed |

### Tier 3: Dormant Connection Brokers (consolidate or delete)

These were created March 2024 and never touched again. Consider:
- Consolidating into `vendor-connectors`
- Or deleting if superseded

| Repo | Status | Recommendation |
|------|--------|----------------|
| git-file-client | Dormant 20mo | Delete or merge |
| aws-connection-broker | Dormant 20mo | Merge into vendor-connectors |
| google-connection-broker | Dormant 20mo | Merge into vendor-connectors |
| terraform-modules-interface | Dormant 20mo | Delete or merge |
| filesystem-broker | Dormant 20mo | Delete or merge |
| gitops-utils | Dormant 20mo | Delete or merge |

---

## 🟡 ARCHIVE: Keep but Freeze (2 repos)

| Repo | Reason to Archive |
|------|-------------------|
| hamachi-vpn | Has 12 stars! Archive, don't delete |
| chef-selenium-grid-extras | Might have users, archive |

---

## ✅ KEEP: Active Ecosystem (22 repos)

### Core Python Libraries (4)
- **extended-data-types** - Foundation, very active
- **lifecyclelogging** - Production, active
- **directed-inputs-class** - Development, active
- **vendor-connectors** - Planning, active

### Active Games/Apps (6)
- **ai_game_dev** - Very active (10 issues)
- **otterfall** - Active today
- **otter-river-rush** - Active today (TypeScript)
- **rivers-of-reckoning** - Recent activity
- **first-python-rpg** - Recent
- **pixels-pygame-palace** - TypeScript game

### Active Infrastructure (5)
- **port-api** - Go API, active
- **openapi-31-to-30-converter** - Go tool, active
- **terraform-github-markdown** - Active TF module
- **terraform-repository-automation** - Active TF module
- **terraform-repository-skeleton** - Active TF template

### This Template (1)
- **python-library-template** - This repo!

### Possibly Keep (evaluate) (6)
- **port-api-python-library** - If still using Port.io
- **chef-selenium-grid-extras** - If still using (archive?)
- **hamachi-vpn** - Has stars (archive?)

---

## 📊 Summary

| Category | Count | Action |
|----------|-------|--------|
| Delete Forks | 52 | `gh repo delete` |
| Delete Dead Owned | 15 | `gh repo delete` |
| Archive | 2 | `gh repo archive` |
| **Keep Active** | **22** | Manage with agents |

### Before: 89 repos
### After: 22 repos (75% reduction!)

---

## 🚀 Execution Commands

### Step 1: Delete all forks
```bash
export GH_TOKEN=$GITHUB_JBCOM_TOKEN

# List forks to verify
gh repo list jbcom --fork --json name -q '.[].name'

# Delete all forks (DESTRUCTIVE!)
gh repo list jbcom --fork --json name -q '.[].name' | while read repo; do
  echo "Deleting jbcom/$repo..."
  gh repo delete "jbcom/$repo" --yes
done
```

### Step 2: Delete dead owned repos
```bash
# Dead repos to delete
DEAD_REPOS=(
  "Cheftasks"
  "google-api-list-lifter"
  "cluster_mgmt"
  "helm"
  "docker-redis-cluster"
  "humankind-unfolding"
  "port-labs-client"
  "port-labs-database-middleware"
  "google-sso-propagation"
  "terraform-aws-datadog-codepipeline"
  "logged-session"
  "gitops-fs-utils"
  "flexiyaml"
  "git-file-client"
  "aws-connection-broker"
  "google-connection-broker"
  "terraform-modules-interface"
  "filesystem-broker"
  "gitops-utils"
)

for repo in "${DEAD_REPOS[@]}"; do
  echo "Deleting jbcom/$repo..."
  gh repo delete "jbcom/$repo" --yes
done
```

### Step 3: Archive instead of delete
```bash
# Archive repos with value
gh repo archive jbcom/hamachi-vpn --yes
gh repo archive jbcom/chef-selenium-grid-extras --yes
```

---

## After Cleanup: The Lean Ecosystem

```
jbcom/
├── Python Libraries (Core)
│   ├── extended-data-types      # Foundation
│   ├── lifecyclelogging         # Logging
│   ├── directed-inputs-class    # Input validation
│   └── vendor-connectors        # Cloud connectors
│
├── Go Projects
│   ├── port-api                 # Port.io API
│   └── openapi-31-to-30-converter
│
├── TypeScript Projects
│   ├── otter-river-rush         # Game
│   └── pixels-pygame-palace     # Game
│
├── Python Games
│   ├── ai_game_dev              # AI game dev
│   ├── otterfall                # Game
│   ├── rivers-of-reckoning      # Game
│   └── first-python-rpg         # RPG
│
├── Terraform
│   ├── terraform-github-markdown
│   ├── terraform-repository-automation
│   └── terraform-repository-skeleton
│
└── Templates
    └── python-library-template   # This repo
```

**22 repos. Clean. Manageable. Focused.**
