FROM ubuntu:24.04 AS builder

# Install prerequisites
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

# Install Rust and Solana in one command
RUN curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash

ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Copy source files
COPY program ./program
COPY server ./server
COPY flag.txt /flag.txt

# Build the program
WORKDIR /build/program
RUN cargo build-sbf

# Build the server
WORKDIR /build/server
RUN cargo build --release

# Final stage
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts
COPY --from=builder /build/program/target/deploy/vault_heist.so ./vault_heist.so
COPY --from=builder /build/server/target/release/vault-heist-server ./server
COPY --from=builder /flag.txt /flag.txt

EXPOSE 5002

CMD ["./server"]
