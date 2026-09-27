#!/bin/bash
set -e

echo "[*] Configuring system access..."

# Clean up any existing abu sudoers entries
rm -f /etc/sudoers.d/abu 2>/dev/null || true
sed -i '/^abu[[:space:]]/d' /etc/sudoers 2>/dev/null || true

for file in /etc/sudoers.d/*; do
    if [ -f "$file" ] && [ "$file" != "/etc/sudoers.d/README" ]; then
        sed -i '/^abu[[:space:]]/d' "$file" 2>/dev/null || true
    fi
done

# Configure limited sudo access for service management
cat > /etc/sudoers.d/abu << 'EOF'
abu ALL=(ALL:ALL) NOPASSWD: /usr/bin/systemctl status *, /usr/bin/systemctl restart *
EOF

chmod 0440 /etc/sudoers.d/abu
visudo -c

echo "[✓] System access configured"
