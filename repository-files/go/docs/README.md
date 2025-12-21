# Documentation

This directory contains additional documentation for this Go package.

## API Documentation

Go packages are self-documenting via [godoc](https://pkg.go.dev/). View the generated documentation at:

```
https://pkg.go.dev/github.com/jbcom/${PACKAGE_NAME}
```

Or run locally:

```bash
# Install godoc
go install golang.org/x/tools/cmd/godoc@latest

# Run local documentation server
godoc -http=:6060

# Visit http://localhost:6060/pkg/github.com/jbcom/${PACKAGE_NAME}/
```

## Writing Good Documentation

Follow these conventions for consistent, jbcom-branded documentation:

### Package Comments

Every package should have a package comment in `doc.go`:

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

### Type Comments

```go
// Client provides methods for interacting with the API.
//
// A Client must be created using [NewClient] and should be reused
// for multiple requests. It is safe for concurrent use.
type Client struct {
    // ...
}

// NewClient creates a new API client with the given configuration.
//
// If config is nil, default values are used.
func NewClient(config *Config) *Client {
    // ...
}
```

## jbcom Brand Guidelines

See the central [DESIGN-SYSTEM.md](../../always-sync/docs/DESIGN-SYSTEM.md) for:
- Color palette
- Typography standards
- Accessibility requirements

For Go-specific styling in generated documentation, godoc handles rendering
automatically. Focus on writing clear, well-structured comments.

## Additional Resources

- [Effective Go](https://golang.org/doc/effective_go)
- [Go Doc Comments](https://go.dev/doc/comment)
- [pkg.go.dev](https://pkg.go.dev/)
