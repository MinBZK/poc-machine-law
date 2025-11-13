## Multi-stage build for nl-wallet verification_server.
FROM rust:1.91-bullseye AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy nl-wallet source from submodule
COPY nl-wallet /build/nl-wallet

# Build verification_server
WORKDIR /build/nl-wallet/wallet_core
RUN cargo build --release \
    --package verification_server \
    --no-default-features \
    --features "allow_insecure_url,postgres" \
    --bin verification_server
RUN cargo build --release \
    --package verification_server_migrations \
    --bin verification_server_migrations


# Build wallet_ca tool for certificate generation
RUN cargo build --release --bin wallet_ca


## Release stage
FROM debian:bookworm-slim AS release

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    gettext-base \
    openssl \
    vim-common \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy built binaries from builder
COPY --from=builder /build/nl-wallet/wallet_core/target/release/verification_server            /app/verification_server
COPY --from=builder /build/nl-wallet/wallet_core/target/release/verification_server_migrations /app/verification_server_migrations
COPY --from=builder /build/nl-wallet/wallet_core/target/release/wallet_ca                      /app/wallet_ca

# Copy configuration templates and certificates
COPY verification_server/* /app/

# Generate reader certificates at build time
# Note: In production, these should be mounted as secrets. If we cannot properly inject the .key.pem at build time then
# we should move this step to entrypoint.sh and add the ca.regelrecht.reader.key.pem as Secret.
RUN /app/wallet_ca reader \
    --ca-key-file /app/ca.regelrecht.reader.key.pem \
    --ca-crt-file /app/ca.regelrecht.reader.crt.pem \
    --common-name "regelrecht.example.com" \
    --reader-auth-file /app/housing_reader_auth.json \
    --file-prefix /app/housing_reader \
    --force

# Environment variables for postgres connection
# These should be set at runtime via docker run -e or docker-compose
ENV RUST_LOG=info
ENV WALLET_REACHABLE_ADDRESS=127.0.0.1
# TODO, probably, need a public endpoint for the wallet but that shouldn't be written into docker image.

# Expose verification_server ports
# requester
EXPOSE 3010
# wallet
EXPOSE 3009

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
