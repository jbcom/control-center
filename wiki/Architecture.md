# Architecture

## Repository Structure

```
jbcom-control-center/
├── packages/                 # All Python packages
│   ├── extended-data-types/  # Foundation library
│   ├── lifecyclelogging/     # Logging library
│   ├── directed-inputs-class/# Input processing
│   └── vendor-connectors/    # API connectors
├── wiki/                     # Wiki source (synced to GitHub wiki)
├── .github/workflows/        # CI/CD workflows
└── templates/                # Templates for repos
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
Push to main → Tests & lint → Auto-version (YYYY.MM.BUILD) → Build → PyPI
```

## Wiki Flow

```
Edit wiki/ folder → Push to main → github-wiki-action syncs → Wiki updated
```
