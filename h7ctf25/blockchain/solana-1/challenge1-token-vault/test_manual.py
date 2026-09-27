#!/usr/bin/env python3
# Quick test to manually send instructions without the solve program

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 5001))

# Receive everything
data = b""
while b"program pubkey:" not in data:
    chunk = sock.recv(4096)
    data += chunk
    
print(data.decode())
print("\n[*] Sending empty program...")
sock.sendall(b"TEST1234567890123456789012345678\n")  # dummy pubkey  
sock.sendall(b"0\n")  # 0 byte program

# See what happens
while True:
    chunk = sock.recv(4096)
    if not chunk:
        break
    print(chunk.decode(), end='')

sock.close()
