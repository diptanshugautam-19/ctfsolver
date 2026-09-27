#!/bin/bash
# Prepare deployment package for Token Vault challenge

set -e

echo "[*] Preparing deployment package..."

DEPLOY_DIR="deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy Dockerfile
cp challenge/Dockerfile "$DEPLOY_DIR/"
cp challenge/entrypoint.sh "$DEPLOY_DIR/"
chmod +x "$DEPLOY_DIR/entrypoint.sh"
cp challenge/docker-compose.yml "$DEPLOY_DIR/"

# Copy program source
mkdir -p "$DEPLOY_DIR/program"
cp -r program/src "$DEPLOY_DIR/program/"
cp program/Cargo.toml "$DEPLOY_DIR/program/"
cp program/Cargo.lock "$DEPLOY_DIR/program/"

# Copy server source
mkdir -p "$DEPLOY_DIR/server"
cp -r server/src "$DEPLOY_DIR/server/"
cp server/Cargo.toml "$DEPLOY_DIR/server/"
cp server/Cargo.lock "$DEPLOY_DIR/server/"

echo "[*] Creating tarball..."
tar -czf token-vault-deploy.tar.gz "$DEPLOY_DIR"

echo "[+] Deployment package ready: token-vault-deploy.tar.gz"
echo ""
echo "Transfer to server:"
echo "  scp -i ~/.ssh/id_ed25519 token-vault-deploy.tar.gz abu@34.47.248.248:~/Challenges/web3-1/"
echo ""
echo "On server:"
echo "  cd ~/Challenges/web3-1"
echo "  tar -xzf token-vault-deploy.tar.gz"
echo "  cd deploy"
echo "  docker build -t h7ctf/token-vault:latest ."
