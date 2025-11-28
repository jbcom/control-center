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
PR to main (conventional commits) → Tests & lint → Merge →
PSR analyzes commits → Version bump per package → Git tags →
Build → PyPI publish
```

### Version Format
- `YYYYMM.MINOR.PATCH` (e.g., `202511.3.0`)
- Per-package Git tags (e.g., `extended-data-types-v202511.3.0`)

## Wiki Flow

```
Edit wiki/ folder → Push to main → github-wiki-action syncs → Wiki updated
```
