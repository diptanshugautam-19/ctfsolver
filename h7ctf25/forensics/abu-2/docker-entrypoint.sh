#!/bin/sh

# Generate unique flag with UUID
UUID=$(uuidgen)
FLAG_VALUE="H7CTF{n0w_y0u_und3rst4nd_where_th3_n4me_0f_th3_ch4llenge_c0mes_fr0m_${UUID}}"

echo "========================================"
echo "KGF 1.0"
echo "========================================"
echo "Dynamic flag generated for this session"
echo "========================================"

# Export flag as environment variable
export FLAG="$FLAG_VALUE"

echo "Starting challenge server on port 3000..."

# Start Node.js server
exec node server.js
