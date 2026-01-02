# Testing Strategy for Control Center

## Overview
This document outlines the testing strategy for the control-center CLI, including all new features (Imagen, Veo, LLM Proxy).

## Test Coverage Requirements

### 1. Unit Tests (Target: 80%+ coverage)
All packages must have unit tests covering:
- **Happy path**: Normal successful operations
- **Error cases**: Invalid inputs, API failures, network errors
- **Edge cases**: Boundary conditions, empty inputs, nil checks
- **Validation**: Input validation and sanitization

### 2. Integration Tests
- API integration tests with mock responses
- End-to-end CLI command tests
- Provider failover and routing tests

### 3. Test Files Structure
```
pkg/clients/
├── imagen/
│   ├── client.go
│   ├── client_test.go      ✓ Unit tests
│   └── integration_test.go  ✓ Integration tests with mocks
├── veo/
│   ├── client.go
│   ├── client_test.go      ✓ Unit tests
│   └── integration_test.go  ✓ Integration tests with mocks
└── proxy/
    ├── server.go
    ├── server_test.go       ✓ Unit tests
    └── integration_test.go   ✓ Integration tests

cmd/control-center/cmd/
├── imagen.go
├── imagen_test.go           ✓ CLI tests
├── veo.go
└── veo_test.go              ✓ CLI tests
```

## Current Test Coverage

### ✅ Already Tested
- `pkg/clients/ollama` - Has unit tests
- `pkg/clients/github` - Has unit tests
- `pkg/clients/gemini` - Has unit tests (needs API fix)

### 🚧 Needs Testing
- `pkg/clients/imagen` - Has basic tests, needs integration tests
- `pkg/clients/veo` - Has basic tests, needs integration tests
- `pkg/proxy` - No tests yet
- `cmd/control-center/cmd/imagen.go` - No tests yet
- `cmd/control-center/cmd/veo.go` - No tests yet

## Testing Checklist

### For Each New Package:
- [ ] Unit tests for all exported functions
- [ ] Unit tests for all exported types
- [ ] Error handling tests
- [ ] Mock tests for external API calls
- [ ] Integration tests with test fixtures
- [ ] Benchmark tests for performance-critical code

### For Each CLI Command:
- [ ] Test help output
- [ ] Test flag parsing
- [ ] Test success scenarios
- [ ] Test error scenarios
- [ ] Test output formats (JSON, human-readable)
- [ ] Test file I/O operations

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
go test -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run specific package tests
go test -v ./pkg/clients/imagen
go test -v ./pkg/clients/veo
go test -v ./pkg/proxy

# Run integration tests only (with build tag)
go test -v -tags=integration ./...

# Run with race detection
go test -race ./...
```

## Test Data and Fixtures

Create `testdata/` directories for:
- Mock API responses
- Sample configuration files
- Test images/videos (small samples)
- Expected output files

## Mocking Strategy

### For API Clients:
1. Use interfaces for all clients
2. Create mock implementations
3. Use httptest for HTTP endpoints
4. Use gomock or testify/mock for complex scenarios

### Example:
```go
type ImageGenerator interface {
    GenerateImage(ctx context.Context, req *ImageRequest) (*ImageResponse, error)
}

// Mock in tests
type MockImageGenerator struct {
    mock.Mock
}

func (m *MockImageGenerator) GenerateImage(ctx context.Context, req *ImageRequest) (*ImageResponse, error) {
    args := m.Called(ctx, req)
    return args.Get(0).(*ImageResponse), args.Error(1)
}
```

## CI/CD Integration

### GitHub Actions Workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.24'
      - name: Run tests
        run: make test
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.out
```

## Quality Gates

Before merging any PR:
1. ✅ All tests must pass
2. ✅ Coverage must not decrease
3. ✅ No new linting errors
4. ✅ Integration tests must pass
5. ✅ CodeQL scan must pass

## Manual Testing Checklist

For each new feature:
- [ ] Test with valid API keys
- [ ] Test with invalid/missing API keys
- [ ] Test with network failures
- [ ] Test with large inputs
- [ ] Test concurrent operations
- [ ] Test timeout scenarios
- [ ] Test output file creation
- [ ] Test JSON output parsing
- [ ] Test in Docker container
- [ ] Test in GitHub Actions workflow

## Performance Testing

For resource-intensive operations:
- [ ] Benchmark image generation
- [ ] Benchmark video generation
- [ ] Benchmark proxy throughput
- [ ] Memory profiling
- [ ] CPU profiling

```bash
# Run benchmarks
go test -bench=. -benchmem ./...

# Profile memory
go test -memprofile=mem.out ./pkg/clients/imagen
go tool pprof mem.out

# Profile CPU
go test -cpuprofile=cpu.out ./pkg/proxy
go tool pprof cpu.out
```

## Documentation Requirements

Each test file should include:
1. Package-level doc comment explaining test strategy
2. Table-driven tests for multiple scenarios
3. Clear test names describing what is tested
4. Comments for complex test logic
5. Setup/teardown helpers for common operations

## Next Steps

1. ✅ Fix Gemini client API usage
2. ✅ Add comprehensive unit tests for Imagen
3. ✅ Add comprehensive unit tests for Veo
4. ✅ Add unit tests for LLM Proxy
5. ✅ Add integration tests with mocks
6. ✅ Add CLI command tests
7. ✅ Set up coverage reporting
8. ✅ Add performance benchmarks
9. ✅ Document test procedures
10. ✅ Add to CI/CD pipeline
