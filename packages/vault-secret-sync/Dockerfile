# First stage: build the Go application
FROM golang:1.23.4 AS builder

# Install dependencies
RUN apt-get update -y && apt-get install -y curl build-essential unzip gcc make pkg-config

# libsodium version and checksum (from official release)
# SHA256 from: https://download.libsodium.org/libsodium/releases/
ENV LIBSODIUM_VERSION=1.0.18
ENV LIBSODIUM_SHA256=6f504490b342a4f8a4c4a02fc9b866cbef8622d5df4e5452b46be121e46636c1

RUN \
    mkdir -p /tmpbuild/libsodium && \
    cd /tmpbuild/libsodium && \
    curl -L https://download.libsodium.org/libsodium/releases/libsodium-${LIBSODIUM_VERSION}.tar.gz -o libsodium-${LIBSODIUM_VERSION}.tar.gz && \
    echo "${LIBSODIUM_SHA256}  libsodium-${LIBSODIUM_VERSION}.tar.gz" | sha256sum -c - && \
    tar xfvz libsodium-${LIBSODIUM_VERSION}.tar.gz && \
    cd /tmpbuild/libsodium/libsodium-${LIBSODIUM_VERSION}/ && \
    ./configure && \
    make && make check && \
    make install && \
    rm -Rf /tmpbuild/ && \
    ldconfig

# Set the Current Working Directory inside the container
WORKDIR /src

# Copy go.mod and go.sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy the source code into the container
COPY . .

# Run tests
RUN go test ./...

# Build the Go application
RUN go build -o /bin/vss cmd/vss/*.go

# Final stage: minimal runtime image
FROM ubuntu:22.04 as vss

# Install only runtime dependencies (ca-certificates for TLS)
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r vss && useradd -r -g vss vss

# Copy libsodium shared library from builder
COPY --from=builder /usr/local/lib/libsodium* /usr/local/lib/
RUN ldconfig

# Copy the binary
COPY --from=builder /bin/vss /bin/vss

# Switch to non-root user
USER vss

WORKDIR /home/vss

# Command to run the executable
ENTRYPOINT [ "/bin/vss" ]
