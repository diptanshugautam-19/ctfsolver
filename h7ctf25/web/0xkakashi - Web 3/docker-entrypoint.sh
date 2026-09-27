#!/bin/bash
set -euo pipefail

UUID="$(uuidgen)"
FLAG="H7CTF{K4K4SH1_5H4R1NG4N_533_411_${UUID}}"

# write flag file (owner: ctf, mode 0400)
mkdir -p /flag
printf "%s\n" "$FLAG" > /flag/flag.txt
chmod 0400 /flag/flag.txt
chown ctf:ctf /flag/flag.txt

exec gosu ctf sh -c "exec java ${JAVA_OPTS:-} -jar /app/app.jar"