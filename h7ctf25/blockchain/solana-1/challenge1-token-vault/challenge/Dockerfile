# Multi-stage build for Token Vault Challenge
FROM ubuntu:24.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libudev-dev \
    llvm \
    libclang-dev \
    protobuf-compiler \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Solana CLI
RUN curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.com/v1.18.18/install | sh
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"

WORKDIR /build

# Copy program and server source
COPY program ./program
COPY server ./server

# Build the Solana program
WORKDIR /build/program
RUN cargo-build-sbf

# Build the server
WORKDIR /build/server
RUN cargo build --release

# Runtime stage
FROM ubuntu:24.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    socat \
    uuid-runtime \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create ctfuser
RUN useradd -m -s /bin/bash ctfuser

# Copy built artifacts
COPY --from=builder /build/program/target/deploy/token_vault.so /home/ctfuser/
COPY --from=builder /build/server/target/release/token-vault-server /home/ctfuser/

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh

# Set working directory
WORKDIR /home/ctfuser

# Set permissions
RUN chown -R ctfuser:ctfuser /home/ctfuser
RUN chmod +x /entrypoint.sh
RUN chmod +x /home/ctfuser/token-vault-server

# Expose port
EXPOSE 5001

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]
