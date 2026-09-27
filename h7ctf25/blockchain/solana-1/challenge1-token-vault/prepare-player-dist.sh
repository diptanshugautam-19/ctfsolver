#!/bin/bash
# Prepare player distribution package

set -e

echo "[*] Preparing player distribution package..."

DIST_DIR="player-dist"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/token-vault/src"

# Copy lib.rs without helper function comments
cp program/src/lib.rs "$DIST_DIR/token-vault/src/"

# Copy entrypoint as-is
cp program/src/entrypoint.rs "$DIST_DIR/token-vault/src/"

# Create processor.rs without vulnerability comments
sed '/^\/\/ BUG:/d; /^\/\/ This will underflow/d; /^\/\/ What if vault.balance/d' \
    program/src/processor.rs > "$DIST_DIR/token-vault/src/processor.rs"

# Copy Cargo.toml
cp program/Cargo.toml "$DIST_DIR/token-vault/"

# Create tarball
cd "$DIST_DIR"
tar -czf ../token-vault-player.tar.gz token-vault/
cd ..

echo "[+] Player distribution ready: token-vault-player.tar.gz"
echo "[+] Package contains only source code (no README)"
echo "[+] Upload to CTFd and put challenge description in CTFd interface"
