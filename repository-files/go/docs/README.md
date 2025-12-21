# Documentation

This directory contains documentation configuration for this Go package using [doc2go](https://go.abhg.dev/doc2go/).

## Why doc2go?

- **Modern**: Built for Go modules (unlike deprecated godoc)
- **Static**: Generates standalone HTML for GitHub Pages
- **Customizable**: Full CSS branding support
- **pkg.go.dev-like**: Familiar styling with syntax highlighting

## Quick Start

### Installation

```bash
go install go.abhg.dev/doc2go@latest
```

### Generate Documentation

```bash
# Standalone mode (complete site)
doc2go -out docs/api ./...

# With custom CSS branding
doc2go -out docs/api ./...
cp docs/jbcom-doc2go.css docs/api/
# Inject CSS link into generated files (see workflow)
```

### Embed Mode (Full Branding Control)

For maximum branding control, use embed mode with Hugo:

```bash
# Generate embeddable API docs
doc2go -embed -out site/content/api -basename _index.html ./...

# Build with Hugo
cd site && hugo --minify
```

## File Structure

```
docs/
├── README.md              # This file
├── jbcom-doc2go.css       # jbcom brand CSS
├── doc2go.yaml            # doc2go configuration (optional)
└── site/                  # Hugo site (for embed mode)
    ├── config.toml
    ├── static/css/
    ├── layouts/
    └── content/api/       # Generated API docs
```

## Configuration

### doc2go.yaml (Optional)

```yaml
# doc2go configuration
output: docs/api
packages:
  - ./...
```

## jbcom Brand Integration

### Standalone Mode

After generating docs, inject the CSS:

```bash
# Generate docs
doc2go -out docs/api ./...

# Copy branding CSS
cp docs/jbcom-doc2go.css docs/api/custom.css

# Inject CSS link into all HTML files
find docs/api -name "*.html" -exec sed -i 's|</head>|<link rel="stylesheet" href="/custom.css"></head>|' {} \;
```

### Embed Mode with Hugo

1. Create Hugo site in `docs/site/`
2. Use jbcom-themed Hugo config
3. Generate embedded docs into `content/api/`
4. Hugo wraps with branded layout

See `docs/site/` for complete Hugo setup.

## GitHub Actions Deployment

Add to `.github/workflows/docs.yml`:

```yaml
name: Deploy Docs
on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: stable
      
      - name: Install doc2go
        run: go install go.abhg.dev/doc2go@latest
      
      - name: Generate API Docs
        run: |
          doc2go -out docs/api ./...
          cp docs/jbcom-doc2go.css docs/api/custom.css
          # Inject CSS into HTML files
          find docs/api -name "*.html" -exec sed -i 's|</head>|<link rel="stylesheet" href="custom.css"></head>|' {} \;
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/api

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
// Import the package and use the main entry points:
//
//	import "github.com/jbcom/example"
//	
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
// The function is safe for concurrent use.
//
// Example:
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

## jbcom Brand Guidelines

See the central [DESIGN-SYSTEM.md](../../always-sync/docs/DESIGN-SYSTEM.md) for:
- Color palette (Primary: #06b6d4, Background: #0a0f1a)
- Typography (Space Grotesk, Inter, JetBrains Mono)
- Accessibility requirements (WCAG AA)

## Additional Resources

- [doc2go Documentation](https://go.abhg.dev/doc2go/)
- [doc2go GitHub](https://github.com/abhinav/doc2go)
- [pkg.go.dev](https://pkg.go.dev/) - Official Go package documentation
- [Effective Go](https://golang.org/doc/effective_go)
- [Go Doc Comments](https://go.dev/doc/comment)
