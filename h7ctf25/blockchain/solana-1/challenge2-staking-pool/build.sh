#!/bin/bash

set -e

echo "🏗️  Building Challenge 2: Staking Pool"
echo "========================================"
echo

# Build everything inside Docker (multi-stage build)
echo "� Building Docker image (includes program + server compilation)..."
echo "⚠️  This will take several minutes on first build..."
docker build -t h7ctf/staking-pool:latest -f challenge/Dockerfile .

echo
echo "✅ Build complete!"
echo "🚀 Run with: docker run --rm -p 5001:5001 h7ctf/staking-pool:latest"
echo "🔗 Connect: nc localhost 5001"
