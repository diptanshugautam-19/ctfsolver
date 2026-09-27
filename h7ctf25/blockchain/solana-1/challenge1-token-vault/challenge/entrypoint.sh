#!/bin/bash
set -euo pipefail

# Generate dynamic flag with UUID
FLAG="H7CTF{1nt3g3r_und3rfl0w_wr4ps_4r0und_$(uuidgen)}"

# Write flag and restrict permissions
printf '%s\n' "$FLAG" > /home/ctfuser/flag.txt
chown ctfuser:ctfuser /home/ctfuser/flag.txt
chmod 400 /home/ctfuser/flag.txt

cd /home/ctfuser

# Run server as ctfuser
exec su ctfuser -c "./token-vault-server"
