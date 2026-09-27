#!/bin/bash
set -e

UUID=$(uuidgen | cut -c1-8)

echo "H7CTF{r0p_j41l_${UUID}}" > /flag

echo "Starting seccomp-jail challenge on port 1337..."
exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"/app/chal",su=ctfuser

