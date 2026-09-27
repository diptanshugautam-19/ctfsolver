#!/bin/sh

# Generate unique flag with UUID each time container starts
FLAG_VALUE=$(echo "H7CTF{al0ha_m1ddl3ware_m1ddl3ware_m1ddl3ware_$(uuidgen)}" | base64 | base64 | tr -d '\n')
echo "Generated flag: $FLAG_VALUE"

# Export as environment variable (no more file modification!)
export FLAG="$FLAG_VALUE"

echo "Flag set as environment variable, starting server..."

# Start the Next.js standalone server (no pnpm needed!)
exec node server.js
