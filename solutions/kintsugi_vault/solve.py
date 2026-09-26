#!/usr/bin/env python3
"""
Kintsugi Vault solver — automated end-to-end exploit.
Downloads the live instance's current handout archive, inverts the 3-round SPN
guardian agent VM bytecode across all chain shards, recovers the 32-byte Ed25519
custody seed, signs the live challenge nonce, and retrieves the flag.
"""
import io
import itertools
import os
import ssl
import struct
import tarfile
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives.asymmetric import ed25519

TARGET_URL = "https://web-986d60e27fd022f4.web.h7tex.com"
HANDOUT_URL = f"{TARGET_URL}/handout.tar.gz"
ATTEST_URL = f"{TARGET_URL}/attest"
SZ6 = {2, 11, 12, 13}

def fetch_handout():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(HANDOUT_URL)
    with urllib.request.urlopen(req, context=ctx) as resp:
        tar_data = resp.read()
    
    files = {}
    with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile():
                files[os.path.basename(member.name)] = tar.extractfile(member).read()
    return files

def invert_mixing(regs):
    regs[7] ^= regs[2]
    regs[6] ^= regs[1]
    regs[5] ^= regs[0]
    regs[4] ^= regs[7]
    regs[3] ^= regs[6]
    regs[2] ^= regs[5]
    regs[1] ^= regs[4]
    regs[0] ^= regs[3]
    regs[7] ^= regs[0]
    regs[6] ^= regs[7]
    regs[5] ^= regs[6]
    regs[4] ^= regs[5]
    regs[3] ^= regs[4]
    regs[2] ^= regs[3]
    regs[1] ^= regs[2]
    regs[0] ^= regs[1]

def invert_shard(raw_bytes, op_map):
    tlen = struct.unpack("<H", raw_bytes[8:10])[0]
    plen = struct.unpack("<H", raw_bytes[10:12])[0]
    sbox = raw_bytes[0x32+tlen : 0x32+tlen+256]
    code = raw_bytes[0x32+tlen+256 : 0x32+tlen+256+plen]
    inv_sbox = {sbox[i]: i for i in range(256)}
    
    ip = 0
    ops = []
    while ip < len(code):
        raw = code[ip]
        v = op_map[raw]
        sz = 6 if v in SZ6 else (1 if v == 0 else 3)
        ops.append((ip, v, code[ip:ip+sz]))
        if v == 0: break
        ip += sz
        
    sbox_rounds = []
    cur_sbox = []
    for i, (ip, v, chunk) in enumerate(ops):
        if v == 10:
            cur_sbox.append((ip, chunk[1], chunk[2]))
            if len(cur_sbox) == 8:
                sbox_rounds.append((i - 7, cur_sbox))
                cur_sbox = []
                
    input_ops = ops[:sbox_rounds[0][0]]
    input_xori = {chunk[1]: struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in input_ops if v == 13}
    input_andi = {chunk[1]: struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in input_ops if v == 12}
    
    eq_vals = [struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in ops if v == 11]
    r = list(eq_vals)
    
    r1_xori = [struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in ops[sbox_rounds[0][0]+8 : sbox_rounds[1][0]] if v == 13]
    r2_xori = [struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in ops[sbox_rounds[1][0]+8 : sbox_rounds[2][0]] if v == 13]
    r3_xori = [struct.unpack("<I", chunk[2:6])[0] for ip, v, chunk in ops[sbox_rounds[2][0]+8 :] if v == 13]
    
    for i in range(8): r[i] ^= r3_xori[i]
    invert_mixing(r)
    for i in range(8): r[i] = inv_sbox[r[i]]
    
    for i in range(8): r[i] ^= r2_xori[i]
    invert_mixing(r)
    for i in range(8): r[i] = inv_sbox[r[i]]
    
    for i in range(8): r[i] ^= r1_xori[i]
    invert_mixing(r)
    for i in range(8): r[i] = inv_sbox[r[i]]
    
    key_choices = []
    for reg_idx in range(8):
        val = r[reg_idx]
        if reg_idx in input_andi:
            mask = input_andi[reg_idx]
            xor_val = input_xori[reg_idx]
            cleared_bits = [bit for bit in range(8) if not (mask & (1 << bit))]
            cands = []
            for combo in range(1 << len(cleared_bits)):
                v = val
                for j, bit in enumerate(cleared_bits):
                    if (combo >> j) & 1: v |= (1 << bit)
                cands.append(v ^ xor_val)
            key_choices.append(cands)
        else:
            key_choices.append([val])
    return [bytes(p) for p in itertools.product(*key_choices)]

def main():
    print("[*] Fetching live instance handout...")
    files = fetch_handout()
    target_pubkey = files["pubkey.bin"]
    manifest = files["MANIFEST.txt"].decode()
    start_cid = [line.split(":")[1].strip() for line in manifest.splitlines() if "chain start:" in line][0]
    
    shards = {f[:-6]: data for f, data in files.items() if f.endswith(".shard")}
    
    # Classify chain shards
    f_start = start_cid
    f_term = [cid for cid, d in shards.items() if d[5] == 2][0]
    intermediates = [cid for cid, d in shards.items() if d[5] == 0 and len(set(d[0x32:0x32+struct.unpack("<H", d[8:10])[0]])) < 256]
    
    print(f"[+] Start: {f_start[:8]}, Term: {f_term[:8]}, Intermediates: {[c[:8] for c in intermediates]}")
    
    # Reconstruct opmaps
    op_maps = {}
    # Start shard has inline table
    d_st = shards[f_start]
    tlen_st = struct.unpack("<H", d_st[8:10])[0]
    tbl_st = d_st[0x32 : 0x32+tlen_st]
    code_st = d_st[0x32+tlen_st+256 : 0x32+tlen_st+256+struct.unpack("<H", d_st[10:12])[0]]
    
    ip = 0
    m_st = {}
    while ip < len(code_st):
        raw = code_st[ip]
        v = tbl_st[raw]
        m_st[raw] = v
        sz = 6 if v in SZ6 else (1 if v == 0 else 3)
        if v == 0: break
        ip += sz
    op_maps[f_start] = m_st
    
    # Other shards
    for cid in intermediates + [f_term]:
        d = shards[cid]
        tlen = struct.unpack("<H", d[8:10])[0]
        code = d[0x32+tlen+256 : 0x32+tlen+256+struct.unpack("<H", d[10:12])[0]]
        loadk = code[0]
        xori = code[0x18]
        andi = code[0x1e]
        for s_ip in range(0x18, 0x80, 6):
            if all(code[s_ip+i*3+1] == i and code[s_ip+i*3+2] == i for i in range(8)):
                sbox = code[s_ip]
                sbox_ip = s_ip
                break
        xorr = code[sbox_ip + 24]
        eq = code[0x258]
        halt = code[-1]
        movr = code[0x255]
        op_maps[cid] = {loadk: 1, xori: 13, andi: 12, sbox: 10, xorr: 4, movr: 3, eq: 11, halt: 0}
        
    keys_start = invert_shard(shards[f_start], op_maps[f_start])
    keys_mid1 = invert_shard(shards[intermediates[0]], op_maps[intermediates[0]])
    keys_mid2 = invert_shard(shards[intermediates[1]], op_maps[intermediates[1]])
    keys_term = invert_shard(shards[f_term], op_maps[f_term])
    
    print("[*] Resolving 32-byte custody seed against instance public key...")
    matched_seed = None
    for k1 in keys_start:
        for k2 in keys_mid1:
            p1 = k1 + k2
            for k3 in keys_mid2:
                p2 = p1 + k3
                for k4 in keys_term:
                    seed = p2 + k4
                    if ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw() == target_pubkey:
                        matched_seed = seed
                        break
                if matched_seed: break
            if matched_seed: break
        if matched_seed: break
        
    if not matched_seed:
        for k1 in keys_start:
            for k2 in keys_mid2:
                p1 = k1 + k2
                for k3 in keys_mid1:
                    p2 = p1 + k3
                    for k4 in keys_term:
                        seed = p2 + k4
                        if ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw() == target_pubkey:
                            matched_seed = seed
                            break
                    if matched_seed: break
                if matched_seed: break
            if matched_seed: break
            
    assert matched_seed is not None, "Failed to match custody seed!"
    print(f"[+] Custody Seed Recovered: {matched_seed.hex()}")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(ATTEST_URL)
    with urllib.request.urlopen(req, context=ctx) as resp:
        nonce_hex = resp.read().decode().strip()
    print(f"[+] Challenge Nonce: {nonce_hex}")
    
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(matched_seed)
    sig_hex = priv.sign(bytes.fromhex(nonce_hex)).hex()
    
    data = urllib.parse.urlencode({"nonce": nonce_hex, "sig": sig_hex}).encode("utf-8")
    post_req = urllib.request.Request(ATTEST_URL, data=data, method="POST")
    with urllib.request.urlopen(post_req, context=ctx) as resp:
        body = resp.read().decode().strip()
        print(f"\n[+] Flag: {body}")
        return body

if __name__ == "__main__":
    main()
