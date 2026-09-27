#!/bin/sh

# Generate unique flag with UUID
UUID=$(uuidgen)
FLAG_VALUE="H7CTF{w3ll_w3ll_w3ll_s0meone_h4s_4_g00dy_2_eyes_${UUID}}"

echo "========================================"
echo "KGF 2.0"
echo "========================================"
echo "Dynamic flag generated for this session"
echo "========================================"

# Export flag as environment variable
export FLAG="$FLAG_VALUE"

echo "Starting challenge server on port 3000..."

# Start Node.js server
exec node server.js
