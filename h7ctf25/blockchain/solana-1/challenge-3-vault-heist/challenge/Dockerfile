FROM ubuntu:24.04 AS builder

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

RUN curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash
ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

COPY program ./program
COPY server ./server

WORKDIR /build/program
RUN cargo-build-sbf

WORKDIR /build/server
RUN cargo build --release

FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    socat \
    uuid-runtime \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ctfuser

COPY --from=builder /build/program/target/deploy/vault_heist.so /home/ctfuser/vault_heist.so
COPY --from=builder /build/server/target/release/vault-heist-server /home/ctfuser/vault-heist-server
COPY entrypoint.sh /entrypoint.sh

WORKDIR /home/ctfuser

RUN chown -R ctfuser:ctfuser /home/ctfuser
RUN chmod +x /entrypoint.sh
RUN chmod +x /home/ctfuser/vault-heist-server

EXPOSE 5003

ENTRYPOINT ["/entrypoint.sh"]
