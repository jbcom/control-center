# Go Copilot Instructions

## Environment Setup

### Go Version
Check `go.mod` for required version.
```bash
go version  # Should match go.mod
```

### Dependencies
```bash
# Download dependencies
go mod download

# Tidy dependencies
go mod tidy

# Verify dependencies
go mod verify
```

## Development Commands

### Testing (ALWAYS run tests)
```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run with coverage
go test -cover ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run specific test
go test -v -run TestFunctionName ./path/to/package

# Run benchmarks
go test -bench=. ./...
```

### Linting
```bash
# Using golangci-lint (preferred)
golangci-lint run

# Fix issues where possible
golangci-lint run --fix

# Run specific linters
golangci-lint run --enable=gofmt,govet,errcheck
```

### Building
```bash
# Build binary
go build -o bin/app ./cmd/app

# Build with version info
go build -ldflags="-X main.version=$(git describe --tags)" ./cmd/app

# Cross-compile
GOOS=linux GOARCH=amd64 go build -o bin/app-linux ./cmd/app
```

### Formatting
```bash
# Format code (always do this)
go fmt ./...

# More thorough formatting
gofumpt -w .
```

## Code Patterns

### Package Structure
```go
package mypackage

import (
    // Standard library first
    "context"
    "fmt"

    // External packages
    "github.com/pkg/errors"

    // Internal packages last
    "github.com/org/repo/internal/config"
)
```

### Error Handling
```go
// Always handle errors explicitly
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}

// Custom error types
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

// Sentinel errors
var ErrNotFound = errors.New("not found")
```

### Context Usage
```go
// Always pass context as first parameter
func ProcessData(ctx context.Context, data []byte) error {
    // Check for cancellation
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    // Process...
    return nil
}
```

### Testing Patterns
```go
package mypackage_test

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestProcessor_Process(t *testing.T) {
    t.Run("valid input", func(t *testing.T) {
        p := NewProcessor()
        result, err := p.Process([]byte("valid"))
        
        require.NoError(t, err)
        assert.Equal(t, expected, result)
    })
    
    t.Run("invalid input", func(t *testing.T) {
        p := NewProcessor()
        _, err := p.Process(nil)
        
        assert.ErrorIs(t, err, ErrInvalidInput)
    })
}

// Table-driven tests
func TestValidate(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"valid", "good", false},
        {"empty", "", true},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := Validate(tt.input)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

### Interface Design
```go
// Small interfaces
type Reader interface {
    Read(ctx context.Context, id string) (*Item, error)
}

type Writer interface {
    Write(ctx context.Context, item *Item) error
}

// Compose interfaces
type Repository interface {
    Reader
    Writer
}
```

## Common Issues

### "undefined" errors
```bash
# Ensure all files are built
go build ./...
```

### Import cycle
- Move shared types to a separate package
- Use interfaces to break dependencies

### Test not finding package
```go
// Use _test suffix for external tests
package mypackage_test  // Can only access exported symbols
package mypackage       // Can access unexported symbols (internal tests)
```

## File Structure
```
cmd/
├── app/
│   └── main.go        # Application entry point
internal/
├── config/            # Configuration (not exported)
├── handlers/          # HTTP/gRPC handlers
└── repository/        # Data access
pkg/
├── client/            # Exported client library
└── models/            # Exported models
```
