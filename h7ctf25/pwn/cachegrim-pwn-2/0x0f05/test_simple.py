#!/usr/bin/env python3
"""
Simple test script to verify 0x0f05 challenge works
"""
from pwn import *

context.arch = 'amd64'

# Simple NOP shellcode for testing
shellcode = b'\x90' * 10  # Just NOPs

print("[*] Connecting to localhost:9999...")
p = remote("localhost", 9999)

print("[*] Receiving initial prompt...")
data = p.recv(timeout=2)
print(f"[+] Received: {data}")

print("[*] Sending NOP shellcode...")
p.sendline(b'90' * 10)  # Hex for NOPs

print("[*] Receiving response...")
response = p.recvall(timeout=5)
print(f"[+] Response: {response}")

p.close()
