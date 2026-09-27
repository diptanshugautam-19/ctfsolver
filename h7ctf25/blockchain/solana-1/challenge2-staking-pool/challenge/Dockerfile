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
RUN curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Copy source files
COPY program ./program
COPY server ./server

# Build program
WORKDIR /build/program
RUN cargo-build-sbf

# Build server
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

# Copy binaries from builder
COPY --from=builder /build/program/target/deploy/staking_pool.so /home/ctfuser/
COPY --from=builder /build/server/target/release/staking-pool-server /home/ctfuser/
COPY entrypoint.sh /entrypoint.sh

WORKDIR /home/ctfuser

RUN chown -R ctfuser:ctfuser /home/ctfuser
RUN chmod +x /entrypoint.sh
RUN chmod +x /home/ctfuser/staking-pool-server

EXPOSE 5001

ENTRYPOINT ["/entrypoint.sh"]
