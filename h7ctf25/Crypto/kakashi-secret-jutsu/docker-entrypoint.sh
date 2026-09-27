#!/bin/bash
set -e

# Generate dynamic UUID for flag
UUID=$(uuidgen)

# Set flag with dynamic UUID
export FLAG="H7CTF{K4K4SH1_5H4R1NG4N_\$33_411_${UUID}}"

echo "Starting Kakashi's Secret Jutsu challenge on port 10000..."

# Start the server
exec python3 /app/source.py
