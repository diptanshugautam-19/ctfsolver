#!/bin/bash

FLAG="h7ctf{0v3rfl0w_\$ucc3ss_$(uuidgen)}"
echo "$FLAG" > /app/flag.txt
chmod 644 /app/flag.txt
exec socat TCP-LISTEN:5000,reuseaddr,fork EXEC:"/app/overflow",pty,stderr
