#!/usr/bin/env bash
set -e

echo "[+] Updating apt repositories..."
sudo apt-get update -y

echo "[+] Installing system analysis and forensics tools..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    binwalk \
    libimage-exiftool-perl \
    tshark \
    steghide \
    gdb \
    gdb-multiarch \
    ltrace \
    strace \
    xxd \
    file \
    curl \
    netcat-openbsd \
    libssl-dev \
    libffi-dev

echo "[+] Installing ruby & zsteg..."
sudo apt-get install -y ruby ruby-dev
sudo gem install zsteg

echo "[+] Installing GEF for gdb..."
bash -c 'wget -q -O- https://gef.blah.cat/sh' | bash || true

echo "[+] Creating CTF Python venv..."
python3 -m venv "$HOME/.ctf-venv"
source "$HOME/.ctf-venv/bin/activate"

echo "[+] Installing CTF Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[+] WSL CTF environment setup complete!"
