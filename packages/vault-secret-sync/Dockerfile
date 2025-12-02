# Build stage
FROM golang:1.23.4-alpine AS builder

# Install git for go mod download (some deps use git)
RUN apk add --no-cache git ca-certificates

WORKDIR /src

# Copy go.mod and go.sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy the source code
COPY . .

# Note: Tests are run in CI separately (some require CGO/libsodium)

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /bin/vss cmd/vss/*.go

# Final stage - minimal image
FROM alpine:3.20

# Install ca-certificates for TLS
RUN apk add --no-cache ca-certificates

# Create non-root user
RUN addgroup -S vss && adduser -S vss -G vss

# Copy the binary
COPY --from=builder /bin/vss /bin/vss

# Switch to non-root user
USER vss

WORKDIR /home/vss

ENTRYPOINT ["/bin/vss"]
