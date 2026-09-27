#!/bin/bash

FLAG="H7CTF{qu4ntum_h34p_3nT4ngl3m3nt_$(uuidgen)}"

echo "$FLAG" > /home/ctfuser/flag.txt
chmod 644 /home/ctfuser/flag.txt
chown ctfuser:ctfuser /home/ctfuser/flag.txt

exec socat -T60 TCP-LISTEN:9999,reuseaddr,fork EXEC:"/home/ctfuser/quantum_memory",stderr
