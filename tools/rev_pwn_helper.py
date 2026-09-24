"""
rev_pwn_helper.py - Scaffolds and helpers for Reverse Engineering & PWN challenges.

Features:
  - Cyclic pattern generation and offset lookup (De Bruijn sequence)
  - Z3 SMT constraint solving template generator
  - Scoped Pwntools exploit skeleton generator
"""

import string


def cyclic_pattern(length: int = 300) -> bytes:
    """Generate a 4-byte De Bruijn cyclic sequence."""
    pattern = bytearray()
    charset = string.ascii_uppercase
    for a in charset:
        for b in string.ascii_lowercase:
            for c in string.digits:
                pattern.extend(f"{a}{b}{c}".encode('ascii'))
                if len(pattern) >= length:
                    return bytes(pattern[:length])
    return bytes(pattern[:length])


def cyclic_offset(sub: bytes, length: int = 2000) -> int:
    """Locate the offset of a 4-byte or 8-byte substring in the cyclic sequence."""
    seq = cyclic_pattern(length)
    if isinstance(sub, str):
        sub = sub.encode('ascii')
    # If passed as hex integer representation (e.g. from $rsp)
    if len(sub) == 8 and all(c in b"0123456789abcdefABCDEF" for c in sub):
        try:
            sub = bytes.fromhex(sub.decode('ascii'))[::-1]
        except Exception:
            pass
    return seq.find(sub)


def generate_pwn_template(target_host: str = "127.0.0.1", target_port: int = 1337, binary_path: str = "./vuln") -> str:
    """Generate an exploit template utilizing scoped connections."""
    return f'''#!/usr/bin/env python3
"""
Exploit template for {binary_path}
"""
import sys
import os
from pwn import *

# Enforce target scope check
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tools.scope_guard import validate_target

HOST = "{target_host}"
PORT = {target_port}
BINARY = "{binary_path}"

elf = context.binary = ELF(BINARY, checksec=False) if os.path.exists(BINARY) else None

def get_target():
    if args.REMOTE:
        validate_target(HOST, PORT)
        return remote(HOST, PORT)
    else:
        return process(BINARY)

def main():
    io = get_target()
    
    # Exploit payload construction
    offset = 40
    payload = b"A" * offset
    
    io.sendline(payload)
    io.interactive()

if __name__ == "__main__":
    main()
'''


def generate_z3_template(input_length: int = 32) -> str:
    """Generate an SMT constraint solver template using Z3."""
    return f'''#!/usr/bin/env python3
"""
Z3 Constraint Solver Template for Keygen / Validation Logic
"""
from z3 import *

def solve():
    s = Solver()
    
    # Define flag/key characters
    chars = [BitVec(f'c_{{i}}', 8) for i in range({input_length})]
    
    # Printable ASCII constraints
    for c in chars:
        s.add(c >= 0x20, c <= 0x7e)
        
    # Standard prefix constraint: flag{{...}}
    prefix = b"flag{{"
    for i, b in enumerate(prefix):
        s.add(chars[i] == b)
    s.add(chars[-1] == ord('}}'))
    
    # === Add challenge-specific mathematical constraints below ===
    # Example: s.add(chars[5] ^ chars[6] == 0x42)
    
    if s.check() == sat:
        m = s.model()
        solution = bytes([m[c].as_long() for c in chars])
        print(f"[+] Solved: {{solution.decode('utf-8', errors='ignore')}}")
        return solution
    else:
        print("[-] Unsatisfiable constraints.")
        return None

if __name__ == "__main__":
    solve()
'''


if __name__ == "__main__":
    print("Cyclic sample (64 bytes):", cyclic_pattern(64).decode())
