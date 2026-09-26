#!/usr/bin/env python3
"""
solve.py - Automated Z3 SMT Solver for Vault Guardian
"""
import sys
import os
import json
import time
from z3 import *

def solve():
    start_time = time.time()
    s = Solver()
    
    # 16 body characters
    body = [BitVec(f'b_{i}', 16) for i in range(16)]
    
    # Printable ASCII constraint
    for b in body:
        s.add(b >= 0x20, b <= 0x7e)
        
    # Sum check
    s.add(Sum(body) == 1458)
    
    # Challenge constraints
    s.add((body[0] ^ body[1]) == 0x49)
    s.add((body[2] + body[3]) == 210)
    s.add((body[4] ^ body[5]) == 0x46)
    s.add((body[6] * 3 - body[7]) == 210)
    s.add((body[8] ^ body[9]) == 0x58)
    s.add((body[10] + body[11] * 2) == 311)
    s.add((body[12] ^ body[13]) == 0x07)
    s.add((body[14] + body[15]) == 82)
    
    # Fixed substring constraints
    prefix_body = b"z3_s"
    for i, c in enumerate(prefix_body):
        s.add(body[i] == c)
        
    mid_body = b"k3y_"
    for i, c in enumerate(mid_body):
        s.add(body[8 + i] == c)
        
    s.add(body[14] == ord('1'))
    s.add(body[4] == ord('0'))
    s.add(body[6] == ord('l'))

    if s.check() == sat:
        m = s.model()
        recovered_body = bytes([m[b].as_long() for b in body]).decode('latin-1')
        flag = f"flag{{{recovered_body}}}"
        print(f"[+] Recovered Flag: {flag}")
        
        # Save flag
        with open("flag.txt", "w", encoding="utf-8") as f:
            f.write(flag + "\n")
            
        elapsed = round(time.time() - start_time, 2)
        
        # Write structured audit log
        audit_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "challenge": "sample_rev_keygen",
            "category": "rev",
            "tool": "z3_solver",
            "flag": flag,
            "status": "solved",
            "elapsed_seconds": elapsed
        }
        
        solutions_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audit_path = os.path.join(solutions_dir, "audit_log.jsonl")
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")
            
        return flag
    else:
        print("[-] Unsatisfiable constraints")
        return None

if __name__ == "__main__":
    solve()
