#!/bin/bash

FLAG="H7CTF{m4ury4n_p|114r_c|ph3r_321|8C3_$(uuidgen)}"

echo "$FLAG" > /home/ctfuser/flag.txt
chmod 644 /home/ctfuser/flag.txt

cd /home/ctfuser

exec socat -T60 TCP-LISTEN:9999,reuseaddr,fork EXEC:"su ctfuser -c ./imperial_archive",stderr
