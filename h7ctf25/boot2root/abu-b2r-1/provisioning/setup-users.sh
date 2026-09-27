#!/bin/bash
set -e

echo "[*] Creating CTF user and setting up flags..."

# Create abu (low-privileged user) - skip if exists
if ! id "abu" &>/dev/null; then
    useradd -m -s /bin/bash abu
fi
echo "abu:mobydockisthewhaleindocker" | chpasswd

# Create home directory structure
mkdir -p /home/abu/{.ssh,Documents,Downloads}
chown -R abu:abu /home/abu

# Add user to docker group (for later exploitation) - if docker is installed
if getent group docker > /dev/null 2>&1; then
    usermod -aG docker abu
    echo "[*] Added abu to docker group"
else
    echo "[*] Docker group not found - will be added later by docker-setup"
fi

echo "[*] Placing flags..."

# Flag 1: In Docker container (already created in docker setup)
# This will be found after exploiting the Docker API
# Located in the flag-container: /flag1.txt
echo "H7CTF{d0ck3r_4p1_3xp0s3d_w1th0ut_4uth_1s_d34dly_d4ng3r0us}" > /tmp/flag1.txt

# Flag 2: User privilege (in abu's home)
cat > /home/abu/flag2.txt << 'EOF'
H7CTF{c0nt41n3r_br34k0ut_pr1v1l3g3d_3sc4p3_t0_h0st_succ3ssful}
EOF

chown abu:abu /home/abu/flag2.txt
chmod 600 /home/abu/flag2.txt

# Flag 3: Root privilege (in /root)
cat > /root/flag3.txt << 'EOF'
H7CTF{d0ck3r_esc4p3_v1a_n4m3sp4c3_sh4r1ng_and_nsent3r}
EOF

chmod 600 /root/flag3.txt

# Create some realistic files for the user
cat > /home/abu/.bash_history << 'EOF'
ls -la
cd Documents
cat meeting-notes.txt
python3 --version
exit
EOF

chown abu:abu /home/abu/.bash_history

# Create some basic documents
cat > /home/abu/Documents/meeting-notes.txt << 'EOF'
Q4 Planning Meeting - October 2025

Attendees: Dev Team, Ops Team
Topics:
- Infrastructure scaling plans
- Security audit scheduled for Nov
- New monitoring dashboard deployment

Action items:
- Review current service configurations
- Update documentation
- Schedule training sessions
EOF

chown -R abu:abu /home/abu/Documents

echo "[✓] Users and flags configured!"
echo "[✓] flag1.txt: Container access"
echo "[✓] flag2.txt: /home/abu/flag2.txt"
echo "[✓] flag3.txt: /root/flag3.txt"
echo "[✓] CTF User: abu / mobydockisthewhaleindocker"
