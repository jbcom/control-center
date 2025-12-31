---
title: "Commands"
weight: 2
---

# Commands Reference

Control Center provides several commands for AI-powered repository management.

## Global Flags

All commands support these flags:

| Flag | Description | Default |
|------|-------------|---------|
| `--config` | Config file path | `~/.control-center.yaml` |
| `--log-level` | Log level | `info` |
| `--log-format` | Log format (text/json) | `text` |
| `--dry-run` | Run without making changes | `false` |

## gardener

Enterprise-level cascade orchestration.

```bash
control-center gardener [flags]
```

### Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--target` | Target: all, org-name, or org/repo | `all` |
| `--decompose` | Cascade to repository level | `false` |
| `--backlog` | Process stale PRs/issues | `true` |

### Examples

```bash
# Run for all organizations
control-center gardener --target all

# Run for specific organization
control-center gardener --target extended-data-library

# Dry run
control-center gardener --target all --dry-run
```

### What it does

1. **Discovers** organizations from `org-registry.json`
2. **Auto-heals** control centers (missing files, misconfigs)
3. **Processes backlog** (stale PRs, unassigned issues)
4. **Decomposes** (optionally triggers org-level gardeners)

---

## curator

Nightly triage of issues and PRs with AI routing.

```bash
control-center curator --repo <owner/name> [flags]
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--repo` | Repository (owner/name) | Yes |

### Examples

```bash
# Curate a repository
control-center curator --repo jbcom/control-center

# Dry run
control-center curator --repo jbcom/control-center --dry-run
```

### What it does

1. **Lists** open issues without triage labels
2. **Analyzes** each issue with Ollama
3. **Routes** to appropriate agent:
   - `ollama` - Quick fixes, single file
   - `jules` - Multi-file refactoring
   - `cursor` - Complex debugging
   - `human` - Ambiguous/sensitive

---

## reviewer

AI-powered code review using Ollama.

```bash
control-center reviewer --repo <owner/name> --pr <number> [flags]
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--repo` | Repository (owner/name) | Yes |
| `--pr` | Pull request number | Yes |

### Examples

```bash
# Review a PR
control-center reviewer --repo jbcom/control-center --pr 123

# With debug output
control-center reviewer --repo jbcom/control-center --pr 123 --log-level debug
```

### What it does

1. **Fetches** PR diff via `gh pr diff`
2. **Analyzes** with Ollama GLM 4.6
3. **Posts** structured review comment with:
   - Summary
   - Issues (severity, category, suggestion)
   - Approval recommendation

---

## fixer

Automated CI failure analysis and suggestions.

```bash
control-center fixer --repo <owner/name> [--pr <number> | --run-id <id>] [flags]
```

### Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--repo` | Repository (owner/name) | Yes |
| `--pr` | Pull request number | One of pr/run-id |
| `--run-id` | Workflow run ID | One of pr/run-id |

### Examples

```bash
# Analyze PR failures
control-center fixer --repo jbcom/control-center --pr 123

# Analyze specific workflow run
control-center fixer --repo jbcom/control-center --run-id 12345678
```

### What it does

1. **Fetches** failure logs via `gh run view --log-failed`
2. **Analyzes** with Ollama GLM 4.6
3. **Posts** fix suggestion comment with:
   - Root cause
   - Specific fix
   - Verification commands

---

## version

Print version information.

```bash
control-center version
```

### Output

```
control-center v1.0.0 (commit: abc123, built: 2024-01-01T00:00:00Z)
```
