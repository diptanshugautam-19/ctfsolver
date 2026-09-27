#!/bin/bash
set -euo pipefail

# Generate dynamic flag with UUID
FLAG="H7CTF{pda_s33d_c0ll1s10n_unlocks_admin_p00l_$(uuidgen)}"

# Write flag and restrict permissions
printf '%s\n' "$FLAG" > /home/ctfuser/flag.txt
chown ctfuser:ctfuser /home/ctfuser/flag.txt
chmod 400 /home/ctfuser/flag.txt

cd /home/ctfuser

# Run server as ctfuser (simplified, works better)
exec su ctfuser -c "./staking-pool-server"
