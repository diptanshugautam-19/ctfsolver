#!/bin/bash
set -e

# Generate dynamic UUID for flag (use first 8 chars only)
UUID=$(uuidgen | cut -c1-8)

# Create flag file with dynamic UUID (as root before switching user)
echo "H7CTF{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_${UUID}}" > /flag.txt
chmod 644 /flag.txt

echo "Starting 0x0f05 shellcode challenge on port 9999..."

# Start TCP server wrapper for chal.py as ctfuser
exec su -s /bin/sh ctfuser -c "python3 /app/server.py"
