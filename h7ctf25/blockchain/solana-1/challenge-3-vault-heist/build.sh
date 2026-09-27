#!/bin/bash
set -e

echo "[*] Building vault heist program..."
cd program
cargo build-sbf
cd ..

echo "[*] Building server..."
cd server
cargo build --release
cd ..

echo "[+] Build complete!"
echo "    Program: program/target/deploy/vault_heist.so"
echo "    Server: server/target/release/vault-heist-server"
