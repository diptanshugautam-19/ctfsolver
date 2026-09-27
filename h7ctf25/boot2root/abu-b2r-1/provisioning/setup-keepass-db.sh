#!/bin/bash
set -e

echo "[+] Setting up SSH credentials and KeePass database..."

# Create directory (hidden in plain sight - system log directory)
mkdir -p /var/log/apt/archives

# Check if KeePass database already exists
if [ -f "/vagrant/.system.kdbx" ]; then
    echo "[✓] KeePass database found! Installing..."
    
    # Check if matching SSH public key exists
    if [ -f "/vagrant/abu_key.pub" ]; then
        echo "[+] Installing SSH public key for abu..."
        mkdir -p /home/abu/.ssh
        cat /vagrant/abu_key.pub > /home/abu/.ssh/authorized_keys
        chmod 700 /home/abu/.ssh
        chmod 600 /home/abu/.ssh/authorized_keys
        chown -R abu:abu /home/abu/.ssh
        echo "[✓] SSH public key installed"
    else
        echo "[!] WARNING: abu_key.pub not found - SSH key authentication won't work!"
    fi
    
    # Install KeePass database
    cp /vagrant/.system.kdbx /var/log/apt/archives/.system.kdbx
    chmod 644 /var/log/apt/archives/.system.kdbx
    echo "[✓] KeePass database installed at /var/log/apt/archives/.system.kdbx"
    echo "[✓] Database password: expectopatronum"
    echo ""
    echo "=============================================="
    echo "  KEEPASS SETUP COMPLETE!"
    echo "=============================================="
    echo "Database location: /var/log/apt/archives/.system.kdbx"
    echo "Container mount: /var/cache/apt/archives/.system.kdbx"
    echo "SSH key: /home/abu/.ssh/authorized_keys"
    echo "=============================================="
    
else
    echo "[!] KeePass database not found at /vagrant/.system.kdbx"
    echo "[+] Generating SSH key pair for first-time setup..."
    
    # Clean up any existing keys
    rm -f /tmp/abu_key /tmp/abu_key.pub
    
    # Generate SSH key pair for abu user (inside VM)
    ssh-keygen -t rsa -b 4096 -f /tmp/abu_key -N "" -C "abu@h7corp.local"
    
    # Install public key
    mkdir -p /home/abu/.ssh
    cat /tmp/abu_key.pub >> /home/abu/.ssh/authorized_keys
    chmod 700 /home/abu/.ssh
    chmod 600 /home/abu/.ssh/authorized_keys
    chown -R abu:abu /home/abu/.ssh
    echo "[+] SSH public key installed for abu user"
    
    # Copy BOTH keys to shared folder (accessible from Windows)
    cp /tmp/abu_key /vagrant/abu_key_generated.txt
    cp /tmp/abu_key.pub /vagrant/abu_key.pub
    echo "[+] SSH keys saved to project folder"
    
    # Clean up /tmp
    rm -f /tmp/abu_key /tmp/abu_key.pub
    
    echo ""
    echo "=============================================="
    echo "  SSH PRIVATE KEY GENERATED!"
    echo "=============================================="
    echo ""
    echo "Location: abu_key_generated.txt (in project root)"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Open abu_key_generated.txt in Notepad"
    echo "2. Copy the ENTIRE contents (including BEGIN/END lines)"
    echo "3. Add to KeePass database:"
    echo "   - Create new database: .system.kdbx"
    echo "   - Password: expectopatronum"
    echo "   - Group: H7Corp Infrastructure"
    echo "   - Entry: Abu SSH Access"
    echo "   - Notes field: Paste the private key"
    echo "   - Add other 5 decoy entries (see docs)"
    echo "4. Save .system.kdbx in project root"
    echo "5. Reprovision: vagrant provision --provision-with keepass-setup"
    echo ""
    echo "=============================================="
fi

echo "[✓] Setup complete!"
