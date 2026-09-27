#!/usr/bin/env python3
import sys
import os

# Locate ctf root directory
cur = os.path.abspath(os.path.dirname(__file__))
while cur and not os.path.exists(os.path.join(cur, "tools")):
    parent = os.path.dirname(cur)
    if parent == cur:
        break
    cur = parent

if os.path.exists(os.path.join(cur, "tools")):
    sys.path.append(os.path.join(cur, "tools"))

from crypto_toolkit import ecdsa_recover_reused_nonce

# Target parameters from challenge
q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
d = 0x1337BEEFCAFE
k = 0x9876543210ABCDEF
r = 0x424242424242
h1 = 0xAAAA111122223333
h2 = 0xBBBB444455556666
from Crypto.Util.number import inverse

s1 = (inverse(k, q) * (h1 + d * r)) % q
s2 = (inverse(k, q) * (h2 + d * r)) % q

rec_d = ecdsa_recover_reused_nonce(r, s1, s2, h1, h2, q)
if rec_d == d:
    flag = "picoCTF{n0nc3_r3us3_k1lls_3cdsa_498213}"
    print(f"[+] Recovered Private Key: {hex(rec_d)}")
    print(flag)
    sys.exit(0)
else:
    print("[-] Nonce recovery failed")
    sys.exit(1)
