#!/bin/bash

set -e

echo "🏗️  Building Challenge 1: Token Vault"
echo "========================================"
echo

# Build everything inside Docker (multi-stage build)
echo "� Building Docker image (includes program + server compilation)..."
echo "⚠️  This will take several minutes on first build..."
docker build -t h7ctf/token-vault:latest -f challenge/Dockerfile .

echo
echo "✅ Build complete!"
echo "🚀 Run with: docker run --rm -p 5000:5000 h7ctf/token-vault:latest"
echo "🔗 Connect: nc localhost 5000"
