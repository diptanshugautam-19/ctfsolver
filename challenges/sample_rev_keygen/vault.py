#!/usr/bin/env python3
"""
Challenge: Vault Guardian (Reverse Engineering / Keygen)
Prompt: Enter the correct flag to unlock the vault.
"""
import sys

def check_flag(flag: str) -> bool:
    if not (flag.startswith("flag{") and flag.endswith("}")):
        return False
    
    body = flag[5:-1]
    if len(body) != 16:
        return False
    
    b = [ord(c) for c in body]
    
    # Validation checks:
    if sum(b) != 1458:
        return False
    if (b[0] ^ b[1]) != 0x49:
        return False
    if (b[2] + b[3]) != 210:
        return False
    if (b[4] ^ b[5]) != 0x46:
        return False
    if (b[6] * 3 - b[7]) != 210:
        return False
    if (b[8] ^ b[9]) != 0x58:
        return False
    if (b[10] + b[11] * 2) != 311:
        return False
    if (b[12] ^ b[13]) != 0x07:
        return False
    if (b[14] + b[15]) != 82:
        return False
    if body[0:4] != "z3_s":
        return False
    if body[8:12] != "k3y_":
        return False
    if b[14] != ord('1'):
        return False
    if b[4] != ord('0'):
        return False
    if b[6] != ord('l'):
        return False

    return True

if __name__ == "__main__":
    inp = input("Enter Vault Flag: ").strip()
    if check_flag(inp):
        print("[+] Vault Unlocked! Flag accepted.")
    else:
        print("[-] Access Denied.")
