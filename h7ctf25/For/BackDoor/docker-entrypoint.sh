#!/bin/bash

# Generate unique flag with UUID
UUID=$(uuidgen)
FLAG_VALUE="H7CTF{D1sc0rd_1s_p0w3rfull_t0_s1mul@t3_C2_${UUID}}"

echo "========================================"
echo "BackDoor Forensics Challenge"
echo "========================================"
echo "Dynamic flag generated for this session"
echo "========================================"

# Export flag as environment variable
export FLAG="$FLAG_VALUE"

echo ""
echo "Starting TCP server on port 3000..."
echo "Users can connect via: nc <host> 3000"
echo ""

# Start TCP server (this keeps the container running)
exec python3 /app/server.py
