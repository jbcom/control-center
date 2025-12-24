# Standard: Multi-Repo Domain Allocation

## Definition

A **project ecosystem** is a collection of repositories that:
1. Share a common namespace prefix (e.g., `nodejs-strata-*`, `*-agentic-*`)
2. Have cross-repository dependencies
3. Present a unified brand/API to users
4. Are actively maintained together

## Qualification Criteria

A project ecosystem qualifies for a **dedicated domain** when it meets ALL of:

| Criterion | Threshold | Example |
|-----------|-----------|---------|
| Repository count | ≥ 3 active repos | strata: 7 repos |
| Cross-dependencies | ≥ 1 repo depends on another | strata-presets → strata |
| Public packages | ≥ 2 published packages | @strata/core, @strata/shaders |
| Documentation need | Would benefit from unified docs | API reference + tutorials |

## Current Qualified Ecosystems

| Ecosystem | Domain | npm Scope | Repos |
|-----------|--------|-----------|-------|
| Strata | `strata.game` | `@strata` | 7 |
| Agentic | `agentic.dev` | `@agentic` | 6 |

## Domain Structure Convention

```
[ecosystem].tld/                   # Apex - main documentation
├── /docs                          # Core concepts
├── /api                           # API reference
└── /examples                      # Usage examples

[package].[ecosystem].tld/         # Per-package subdomain
```

## settings.yml Configuration

Each repository in a qualified ecosystem should have:

```yaml
# .github/settings.yml
repository:
  homepage: https://[package].[ecosystem].tld

pages:
  enabled: true
  build_type: workflow
  cname: [package].[ecosystem].tld
```

## Workflow Template

```yaml
# .github/workflows/docs.yml
name: Deploy Documentation
on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: pnpm install
      - run: pnpm run docs:build
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          cname: '[package].[ecosystem].tld'
```
