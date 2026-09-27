#!/bin/bash
set -e

echo "[*] Setting up Docker privilege escalation environment..."

# Ensure abu is in docker group
if id "abu" &>/dev/null; then
    usermod -aG docker abu
    echo "[✓] User abu added to docker group"
fi

# Pull Alpine image (lightweight, has nsenter)
echo "[*] Pulling Alpine image for privilege escalation..."
docker pull alpine:latest

# Update bash history to show realistic usage
cat >> /home/abu/.bash_history << 'EOF'
ls -la
docker ps
id
EOF

chown abu:abu /home/abu/.bash_history

echo "[✓] Docker privilege escalation environment configured"
echo "[i] User abu can access Docker - nsenter technique available"
