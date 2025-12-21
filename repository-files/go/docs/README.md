# Documentation

This directory contains a complete Hugo-based documentation site with [doc2go](https://go.abhg.dev/doc2go/) 
for API reference generation, fully branded with the jbcom design system.

## Architecture

```
docs/
├── README.md                    # This file
├── jbcom-doc2go.css            # Standalone mode CSS (alternative)
└── site/                        # Hugo site (full branding)
    ├── hugo.toml               # Hugo configuration
    ├── content/
    │   ├── _index.md           # Homepage
    │   └── api/                # doc2go output (generated)
    ├── layouts/
    │   ├── _default/           # Page templates
    │   └── partials/           # Header, sidebar, footer
    └── static/
        ├── css/jbcom.css       # Complete jbcom theme
        └── img/favicon.svg     # jbcom favicon
```

## Quick Start

### Prerequisites

```bash
# Install doc2go
go install go.abhg.dev/doc2go@latest

# Install Hugo (extended version recommended)
# macOS
brew install hugo

# Linux
snap install hugo

# Or download from https://gohugo.io/installation/
```

### Generate and Build

```bash
# 1. Generate API documentation (from project root)
doc2go -embed -out docs/site/content/api -basename _index.md ./...

# 2. Build Hugo site
cd docs/site
hugo --minify

# 3. Output is in docs/site/public/
```

### Local Preview

```bash
cd docs/site
hugo server -D
# Visit http://localhost:1313
```

## GitHub Actions Deployment

Add `.github/workflows/docs.yml`:

```yaml
name: Deploy Documentation
on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # For git info
      
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: stable
      
      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'
          extended: true
      
      - name: Install doc2go
        run: go install go.abhg.dev/doc2go@latest
      
      - name: Generate API Documentation
        run: doc2go -embed -out docs/site/content/api -basename _index.md ./...
      
      - name: Build Hugo Site
        run: |
          cd docs/site
          hugo --minify --baseURL "https://jbcom.github.io/${{ github.event.repository.name }}/"
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/site/public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Customization

### Project-Specific Settings

Edit `site/hugo.toml`:

```toml
baseURL = "https://jbcom.github.io/your-project/"
title = "Your Project Documentation"

[params]
  description = "Your project description"
  github_repo = "https://github.com/jbcom/your-project"
```

### Homepage Content

Edit `site/content/_index.md` to customize the landing page with:
- Installation instructions
- Quick start examples
- Feature highlights

### Navigation

Edit the `[menu]` section in `hugo.toml` to add/remove navigation items.

### Styling

The jbcom theme is in `site/static/css/jbcom.css`. To customize:
- Modify CSS custom properties at the top for colors/fonts
- Add overrides at the bottom for specific elements

## jbcom Brand Guidelines

This site follows the [jbcom Design System](../../always-sync/docs/DESIGN-SYSTEM.md):

| Element | Value |
|---------|-------|
| Primary Color | `#06b6d4` (Cyan) |
| Background | `#0a0f1a` (Dark Navy) |
| Headings | Space Grotesk |
| Body Text | Inter |
| Code | JetBrains Mono |

## Alternative: Standalone Mode

For simpler projects without Hugo, use standalone mode:

```bash
# Generate complete site
doc2go -out docs/api ./...

# Apply branding CSS
cp docs/jbcom-doc2go.css docs/api/custom.css

# Inject CSS into HTML files
find docs/api -name "*.html" -exec sed -i 's|</head>|<link rel="stylesheet" href="custom.css"></head>|' {} \;
```

This produces a pkg.go.dev-like site with jbcom styling, but less branding control than the Hugo approach.

## Writing Good Documentation

### Package Comments

Every package should have a doc comment in `doc.go`:

```go
// Package example provides utilities for demonstrating Go documentation.
//
// This package follows jbcom coding standards and is part of the
// jbcom open source ecosystem.
//
// # Getting Started
//
//	import "github.com/jbcom/example"
//	result := example.Process(input)
//
// # Configuration
//
// The package can be configured via environment variables:
//
//	EXAMPLE_DEBUG=true    Enable debug logging
//	EXAMPLE_TIMEOUT=30s   Set operation timeout
package example
```

### Function Comments

```go
// Process transforms the input according to the configured rules.
//
// It returns an error if the input is invalid or if processing fails.
//
// # Arguments
//
//   - input: The string to process
//
// # Returns
//
// The processed string, or an error if processing fails.
//
// # Example
//
//	result, err := Process("input data")
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Println(result)
func Process(input string) (string, error) {
    // ...
}
```

## Resources

- [doc2go Documentation](https://go.abhg.dev/doc2go/)
- [Hugo Documentation](https://gohugo.io/documentation/)
- [Go Doc Comments](https://go.dev/doc/comment)
- [pkg.go.dev](https://pkg.go.dev/)
