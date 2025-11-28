# Architecture

## Repository Structure

```
jbcom-control-center/
├── packages/                 # All Python packages
│   ├── extended-data-types/  # Foundation library
│   ├── lifecyclelogging/     # Logging library
│   ├── directed-inputs-class/# Input processing
│   └── vendor-connectors/    # API connectors
├── .github/
│   ├── workflows/            # CI/CD workflows
│   └── actions/              # Reusable actions
├── templates/                # Templates for repos
└── .cursor/                  # Cursor configuration
```

## Package Dependencies

```
extended-data-types ← Foundation (no internal deps)
       ↑
       ├── lifecyclelogging
       ├── directed-inputs-class
       └── vendor-connectors ← depends on ALL above
```

## CI/CD Flow

```
Push to main
    ↓
Run tests & lint
    ↓
Auto-generate version (YYYY.MM.BUILD)
    ↓
Build package
    ↓
Publish to PyPI
```

## Documentation Flow

```
Wiki (Source of Truth)
    ↓
Agents read via wiki-cli
    ↓
Agents update via wiki-cli
    ↓
Changes committed to wiki repo
```

## Token Usage

| Token | Purpose | Where |
|-------|---------|-------|
| GITHUB_JBCOM_TOKEN | Local agent operations | Cursor env |
| JBCOM_TOKEN | Cross-repo workflows | GitHub secret |
| CI_GITHUB_TOKEN | CI operations | GitHub secret |
| ANTHROPIC_API_KEY | Claude Code | GitHub secret |
