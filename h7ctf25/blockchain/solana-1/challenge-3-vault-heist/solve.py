#!/usr/bin/env python3
import socket
import os
import re
import hashlib
import base58

HOST = os.getenv("CHALLENGE_HOST", "localhost")
PORT = int(os.getenv("CHALLENGE_PORT", "5003"))
SOLVE_PATH = "solve/target/deploy/vault_heist_solve.so"

def main():
    print("[*] Connecting to challenge server...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("[+] Connected!")
        
        # Read banner and challenge info until we get the "program pubkey:" prompt
        response = b""
        while b"program pubkey:" not in response:
            chunk = s.recv(4096)
            if not chunk:
                print("[!] Server disconnected")
                return
            response += chunk
        
        banner = response.decode('utf-8', errors='ignore')
        print(banner)
        
        # Extract addresses from banner
        user_match = re.search(r'Address:\s+(\w+)', banner)
        program_match = re.search(r'Program ID:\s+(\w+)', banner)
        vault_match = re.search(r'Vault PDA:\s+(\w+)', banner)
        admin_match = re.search(r'Admin:\s+(\w+)', banner)
        
        if not all([user_match, program_match, vault_match, admin_match]):
            print("[!] Failed to extract addresses")
            return
        
        user_pubkey = user_match.group(1)
        program_pubkey = program_match.group(1)
        vault_pubkey = vault_match.group(1)
        admin_pubkey = admin_match.group(1)
        
        print(f"\n[*] Extracted:")
        print(f"  User: {user_pubkey}")
        print(f"  Program: {program_pubkey}")
        print(f"  Vault: {vault_pubkey}")
        print(f"  Admin: {admin_pubkey}\n")
        
        # Load solve program
        print(f"[*] Loading {SOLVE_PATH}...")
        with open(SOLVE_PATH, 'rb') as f:
            solve_data = f.read()
        
        # Generate solve program pubkey
        solve_seed = hashlib.sha256(solve_data).digest()
        solve_pubkey = base58.b58encode(solve_seed).decode('ascii')
        
        # Send solve program pubkey (responding to "program pubkey:" prompt)
        print(f"[*] Sending solve program pubkey: {solve_pubkey}")
        s.sendall(f"{solve_pubkey}\n".encode())
        
        # Wait for "program len:" prompt
        response = b""
        while b"program len:" not in response:
            chunk = s.recv(1024)
            if not chunk:
                print("[!] Server disconnected")
                return
            response += chunk
        
        # Send program length and data
        print(f"[*] Sending solve program ({len(solve_data)} bytes)")
        s.sendall(f"{len(solve_data)}\n".encode())
        s.sendall(solve_data)
        print(f"[+] Sent solve program")
        
        # Wait for instruction prompt
        response = b""
        while b"num accounts:" not in response:
            chunk = s.recv(4096)
            if not chunk:
                print("[!] Server disconnected")
                return
            response += chunk
            print(chunk.decode('utf-8', errors='ignore'), end='')
        
        # Send instruction
        print("\n[*] Sending instruction...")
        s.sendall(b"4\n")  # 4 accounts
        s.sendall(f"ws {user_pubkey}\n".encode())  # user (writable, signer)
        s.sendall(f"x {program_pubkey}\n".encode())  # vault program (readonly)
        s.sendall(f"w {vault_pubkey}\n".encode())  # vault PDA (writable)
        s.sendall(f"w {admin_pubkey}\n".encode())  # admin (writable)
        s.sendall(b"0\n")  # no instruction data
        print("[+] Sent instruction")
        
        # Read results
        print("\n[*] Waiting for results...\n")
        while True:
            data = s.recv(4096)
            if not data:
                break
            print(data.decode('utf-8', errors='ignore'), end='')

if __name__ == "__main__":
    if not os.path.exists(SOLVE_PATH):
        print(f"[!] Error: {SOLVE_PATH} not found!")
        print("[!] Run: cd solve && cargo build-sbf")
        exit(1)
    
    main()
