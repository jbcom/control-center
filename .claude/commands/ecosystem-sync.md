---
allowed-tools: Bash(gh:*),Bash(pip:*),Read,Glob,Grep
description: Check ecosystem health and sync status
---

You're an ecosystem coordinator for the jbcom Python library ecosystem. Check health and sync status across all packages.

ARGUMENTS: $ARGUMENTS

ECOSYSTEM PACKAGES:

1. **extended-data-types** (Foundation)
   - PyPI: extended-data-types
   - Repo: jbcom/extended-data-types
   - No dependencies on other ecosystem packages

2. **lifecyclelogging**
   - PyPI: lifecyclelogging
   - Repo: jbcom/lifecyclelogging
   - Depends on: extended-data-types

3. **directed-inputs-class**
   - PyPI: directed-inputs-class
   - Repo: jbcom/directed-inputs-class
   - Depends on: extended-data-types

4. **vendor-connectors**
   - PyPI: vendor-connectors
   - Repo: jbcom/vendor-connectors
   - Depends on: extended-data-types, lifecyclelogging, directed-inputs-class

CHECKS TO PERFORM:

1. **Public Repo CI Status**
   ```bash
   for repo in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
     echo "=== jbcom/$repo ==="
     gh run list --repo jbcom/$repo --limit 3
   done
   ```

2. **PyPI Version Check**
   ```bash
   pip index versions extended-data-types 2>/dev/null | head -5
   pip index versions lifecyclelogging 2>/dev/null | head -5
   pip index versions vendor-connectors 2>/dev/null | head -5
   ```

3. **Open PRs**
   ```bash
   for repo in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
     gh pr list --repo jbcom/$repo --state open
   done
   ```

4. **Open Issues**
   ```bash
   for repo in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
     gh issue list --repo jbcom/$repo --state open --limit 5
   done
   ```

OUTPUT FORMAT:

Create a summary issue or comment with:
- Overall ecosystem health (green/yellow/red)
- CI status per repo
- PyPI version status
- Open PRs requiring attention
- Open issues requiring attention
- Recommended actions
