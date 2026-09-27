#!/bin/bash

set -e

echo "[*] Building Secure Bytecode Executor..."

make clean

make

echo "[+] Build complete!"
echo "[*] Binary: ./main"

echo "[*] Copying binary to ../deploy/..."
cp main ../deploy/

echo "[+] Ready for deployment!"
