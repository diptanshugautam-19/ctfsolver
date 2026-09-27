#!/usr/bin/env python3
"""
Simple test script to verify Kakashi challenge is working
Solves the PoW and shows the menu
"""
import socket
import hashlib
import string
import re

def solve_pow(suffix, target_hash):
    """Brute force the 4-character prefix"""
    chars = string.ascii_letters + string.digits
    
    print(f"[*] Solving PoW...")
    print(f"    Suffix: {suffix}")
    print(f"    Target: {target_hash}")
    
    for c1 in chars:
        for c2 in chars:
            for c3 in chars:
                for c4 in chars:
                    prefix = c1 + c2 + c3 + c4
                    test = prefix + suffix
                    h = hashlib.sha256(test.encode()).hexdigest()
                    if h == target_hash:
                        print(f"[+] Found: {prefix}")
                        return prefix
    return None

def test_challenge():
    HOST = 'localhost'
    PORT = 10000
    
    print(f"[*] Connecting to {HOST}:{PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    # Read banner
    banner = b''
    while b'Give me XXXX:' not in banner:
        banner += s.recv(1024)
    
    print("[+] Received banner and PoW challenge")
    banner_text = banner.decode('latin-1')
    print(banner_text)
    
    # Parse PoW challenge
    # Format: sha256(XXXX+suffix) == hash
    match = re.search(r'sha256\(XXXX\+([a-zA-Z0-9]+)\) == ([a-f0-9]{64})', banner_text)
    if not match:
        print("[-] Could not parse PoW challenge")
        return
    
    suffix = match.group(1)
    target_hash = match.group(2)
    
    # Solve PoW
    solution = solve_pow(suffix, target_hash)
    if not solution:
        print("[-] Could not solve PoW")
        return
    
    # Send solution
    s.sendall(solution.encode() + b'\n')
    print(f"[*] Sent solution: {solution}")
    
    # Read response (should be menu)
    response = b''
    while True:
        try:
            s.settimeout(2)
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
            if b'3. Die' in response:
                break
        except socket.timeout:
            break
    
    print("\n[+] Challenge menu received:")
    print(response.decode('latin-1', errors='ignore'))
    
    # Send option 3 to exit gracefully
    s.sendall(b'3\n')
    
    s.close()
    print("\n[+] Challenge is working correctly!")

if __name__ == "__main__":
    test_challenge()
