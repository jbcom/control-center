# syntax=docker/dockerfile:1.7

###
# Build a static control-center binary for the requested platform.
###
FROM golang:1.25-bookworm AS builder

ARG TARGETOS=linux
ARG TARGETARCH=amd64
ARG TARGETVARIANT
ARG CGO_ENABLED=0

ARG VERSION=dev
ARG COMMIT=none
ARG DATE=unknown

ENV CGO_ENABLED=${CGO_ENABLED} \
    GOTOOLCHAIN=auto
WORKDIR /src

# Update CA certificates
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY go.mod go.sum ./

# Cache module and build downloads between runs
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

COPY . .

RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    GOOS=${TARGETOS} \
    GOARCH=${TARGETARCH} \
    GOARM=${TARGETVARIANT#v} \
    go build -trimpath \
      -ldflags="-s -w \
        -X github.com/jbcom/control-center/cmd/control-center/cmd.Version=${VERSION} \
        -X github.com/jbcom/control-center/cmd/control-center/cmd.Commit=${COMMIT} \
        -X github.com/jbcom/control-center/cmd/control-center/cmd.Date=${DATE}" \
      -o /out/control-center ./cmd/control-center

###
# Runtime image: tiny BusyBox container that only carries the binary and certs.
###
FROM busybox:1.37.0-musl AS runtime

ARG VERSION=dev

ENV CONTROL_CENTER_VERSION=${VERSION}

LABEL org.opencontainers.image.title="control-center" \
      org.opencontainers.image.description="Enterprise AI orchestration for the jbcom ecosystem" \
      org.opencontainers.image.source="https://github.com/jbcom/control-center" \
      org.opencontainers.image.version=${VERSION}

WORKDIR /app

RUN mkdir -p /etc/ssl/certs
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=builder /out/control-center /usr/local/bin/control-center

# Ensure gh CLI is available (installed in runtime for GitHub operations)
# In production, use a base image with gh or mount it
# For GitHub Actions, gh is pre-installed

ENTRYPOINT ["/usr/local/bin/control-center"]
CMD ["--help"]
