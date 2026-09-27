#!/bin/bash

FLAG="H7CTF{m3m0ry_m4pp1ng_bug5_4r3_tr1cky_70_f1nd_$(uuidgen)}"

echo "$FLAG" > /home/ctfuser/flag.txt
chmod 644 /home/ctfuser/flag.txt
chown ctfuser:ctfuser /home/ctfuser/flag.txt

exec socat -T60 TCP-LISTEN:9999,reuseaddr,fork EXEC:"/home/ctfuser/main",stderr
