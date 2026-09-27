#!/bin/bash
set -e

echo "[*] Installing Docker..."

# Install Docker prerequisites
export DEBIAN_FRONTEND=noninteractive
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    iptables-persistent 2>&1 | grep -v "^$" || true

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt-get update -qq
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>&1 | grep -v "^$" || true

echo "[*] Configuring Docker API exposure..."

# Create Docker daemon configuration with security restrictions
mkdir -p /etc/docker

cat > /etc/docker/daemon.json << 'DAEMON_EOF'
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]
}
DAEMON_EOF

# Create systemd override directory
mkdir -p /etc/systemd/system/docker.service.d

# Configure Docker to expose API on 0.0.0.0:2375 (will be firewalled)
cat > /etc/systemd/system/docker.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --containerd=/run/containerd/containerd.sock
EOF

echo "[*] Docker authorization plugin (deny privileged containers)..."
# Note: We're using daemon.json security options instead of a full plugin
# This provides realistic security hardening that companies actually do

# Enable Docker socket (for local use)
systemctl daemon-reload
systemctl enable docker

# Clean up old userns-remap data if it exists
# This prevents issues when switching from userns-remap to normal mode
if [ -d "/var/lib/docker/100000.100000" ]; then
    echo "[*] Cleaning up old userns-remap data..."
    systemctl stop docker
    rm -rf /var/lib/docker/100000.100000
    # Also clean up any subuid/subgid mappings
    sed -i '/^dockremap:/d' /etc/subuid 2>/dev/null || true
    sed -i '/^dockremap:/d' /etc/subgid 2>/dev/null || true
fi

systemctl restart docker

# Wait for Docker to be ready
sleep 5

echo "[*] Configuring firewall rules..."
# Allow localhost access to Docker API
iptables -A INPUT -i lo -p tcp --dport 2375 -j ACCEPT
# Block external access (but port appears as filtered in nmap)
iptables -A INPUT -p tcp --dport 2375 -j DROP

# Save iptables rules to persist across reboots
iptables-save > /etc/iptables/rules.v4 || true
# Ensure netfilter-persistent service is enabled
systemctl enable netfilter-persistent 2>/dev/null || true
systemctl start netfilter-persistent 2>/dev/null || true

echo "[*] Verifying Docker installation..."
docker --version

# Test Docker API (from localhost)
curl -s http://localhost:2375/version > /dev/null && echo "[✓] Docker API is accessible on localhost:2375"

# Pull some useful images for the challenge
echo "[*] Pulling Docker images..."
docker pull busybox:latest
docker pull ubuntu:latest

# Create a vulnerable container with privileged flag for easy escape
echo "[*] Setting up vulnerable Docker environment..."

# Remove existing containers if they exist
# Force stop and remove to ensure clean state
docker stop pacman 2>/dev/null || true
docker rm -f pacman 2>/dev/null || true

# Clean up any orphaned container data
rm -rf /var/lib/docker/containers/*/pacman* 2>/dev/null || true

# Create flag file on host first (remove if exists as directory)
rm -rf /tmp/.flag1.txt
echo "H7CTF{d0ck3r_4p1_3xp0s3d_w1th0ut_4uth_1s_d34dly_d4ng3r0us}" > /tmp/.flag1.txt
chmod 644 /tmp/.flag1.txt

# Ensure the KeePass directory exists
mkdir -p /var/log/apt/archives
chmod 755 /var/log/apt/archives

# Create a container with the flag and volume mount (read-only, no privileged access)
# Mount host /var/log/apt/archives to container /var/cache/apt/archives (looks normal)
# Using busybox which has nc (netcat) for reverse shells
echo "[*] Creating pacman container..."
docker run -d \
    --name pacman \
    --restart always \
    -v /tmp/.flag1.txt:/flag1.txt:ro \
    -v /var/log/apt/archives:/var/cache/apt/archives:ro \
    --security-opt=no-new-privileges:true \
    busybox:latest \
    sleep infinity

# Verify container is running
sleep 2
if docker ps | grep -q pacman; then
    echo "[✓] Container 'pacman' is running"
else
    echo "[!] WARNING: Container 'pacman' failed to start!"
    echo "[!] Checking logs..."
    docker logs pacman 2>&1 | tail -10
    docker inspect pacman | grep -A 5 "Error"
fi

# Create a systemd service to ensure container is always recreated fresh on boot
echo "[*] Creating systemd service for pacman container..."
cat > /etc/systemd/system/pacman-container.service << 'SYSTEMD_EOF'
[Unit]
Description=Pacman Docker Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
# Always recreate the container fresh on boot
ExecStartPre=/usr/bin/docker rm -f pacman || true
# Ensure flag file exists as a FILE before mounting
ExecStartPre=/bin/bash -c 'rm -rf /tmp/.flag1.txt && echo "H7CTF{d0ck3r_4p1_3xp0s3d_w1th0ut_4uth_1s_d34dly_d4ng3r0us}" > /tmp/.flag1.txt && chmod 644 /tmp/.flag1.txt'
ExecStart=/usr/bin/docker run -d \
    --name pacman \
    --restart always \
    -v /tmp/.flag1.txt:/flag1.txt:ro \
    -v /var/log/apt/archives:/var/cache/apt/archives:ro \
    --security-opt=no-new-privileges:true \
    busybox:latest \
    sleep infinity
ExecStop=/usr/bin/docker stop pacman || true
ExecStopPost=/usr/bin/docker rm -f pacman || true

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

# Enable the service
systemctl daemon-reload
systemctl enable pacman-container.service
echo "[✓] Pacman container service enabled"

# Add abu user to docker group (for container escape exploitation)
if id "abu" &>/dev/null; then
    usermod -aG docker abu
    echo "[✓] Added abu to docker group"
fi

# Add vagrant user to docker group (for testing/debugging)
if id "vagrant" &>/dev/null; then
    usermod -aG docker vagrant
    echo "[✓] Added vagrant to docker group"
fi

echo "[✓] Docker setup complete!"
echo "[✓] Docker API exposed on: http://0.0.0.0:2375"
echo "[✓] Container deployed: pacman"
echo "[✓] Systemd service will ensure container persists across reboots"
