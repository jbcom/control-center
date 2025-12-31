# Control Center Makefile

.PHONY: all build test lint lint-fix deps fmt tidy clean help install

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOTEST=$(GOCMD) test
GOMOD=$(GOCMD) mod
GOFMT=$(GOCMD) fmt
GOLINT=golangci-lint

# Build info
BINARY_NAME=control-center
VERSION?=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT?=$(shell git rev-parse --short HEAD 2>/dev/null || echo "none")
DATE?=$(shell date -u '+%Y-%m-%dT%H:%M:%SZ')
LDFLAGS=-s -w \
	-X github.com/jbcom/control-center/cmd/control-center/cmd.Version=$(VERSION) \
	-X github.com/jbcom/control-center/cmd/control-center/cmd.Commit=$(COMMIT) \
	-X github.com/jbcom/control-center/cmd/control-center/cmd.Date=$(DATE)

all: lint test build

## Build targets
build:
	@mkdir -p bin
	$(GOBUILD) -ldflags "$(LDFLAGS)" -o bin/$(BINARY_NAME) ./cmd/control-center

## Install locally
install:
	$(GOBUILD) -ldflags "$(LDFLAGS)" -o $(GOPATH)/bin/$(BINARY_NAME) ./cmd/control-center

## Test targets
test:
	$(GOTEST) -race -coverprofile=coverage.out ./...

test-verbose:
	$(GOTEST) -v -race -coverprofile=coverage.out ./...

## Lint targets
lint:
	$(GOLINT) run

lint-fix:
	$(GOLINT) run --fix

## Formatting
fmt:
	$(GOFMT) ./...

## Dependency management
tidy:
	$(GOMOD) tidy

deps:
	$(GOMOD) download
	$(GOMOD) tidy

## Docker targets
docker-build:
	docker build -t ghcr.io/jbcom/control-center:dev .

docker-run:
	docker run --rm ghcr.io/jbcom/control-center:dev --help

## Clean targets
clean:
	rm -f $(BINARY_NAME)
	rm -rf bin/
	rm -f coverage.out

## Help
help:
	@echo "Available targets:"
	@echo "  build        - Build the binary to bin/"
	@echo "  install      - Install binary to GOPATH/bin"
	@echo "  test         - Run unit tests with race detection and coverage"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run golangci-lint"
	@echo "  lint-fix     - Run golangci-lint with auto-fix"
	@echo "  fmt          - Format Go code with go fmt"
	@echo "  tidy         - Run go mod tidy"
	@echo "  deps         - Download and tidy dependencies"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker image"
	@echo "  clean        - Clean build artifacts"
