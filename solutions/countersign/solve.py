#!/usr/bin/env python3
"""
Countersign Solver - Reversing / Cryptography
Extracts program image, identifies valid attested edges using MINT oracle,
inverts the 12-round ARX permutation on r0..r3 to recover branch decisions,
and inverts r4, r5 along the unique valid path to emit the flag.
"""

import socket
import struct
import sys

def rol(x, n): return ((x << n) | (x >> (32 - n))) & 0xffffffff
def ror(x, n): return ((x >> n) | (x << (32 - n))) & 0xffffffff

def fwd_round(r0, r1, r2, r3, rot1, rot2, imm1, imm2):
    r0 = (r0 + r1) & 0xffffffff
    r0 = rol(r0, rot1)
    r2 = r2 ^ r0
    r3 = (r3 + r2) & 0xffffffff
    r3 = rol(r3, rot2)
    r1 = r1 ^ r3
    r0 = (r0 + imm1) & 0xffffffff
    r2 = r2 ^ imm2
    return r0, r1, r2, r3

def bwd_round(r0, r1, r2, r3, rot1, rot2, imm1, imm2):
    r2 = r2 ^ imm2
    r0 = (r0 - imm1) & 0xffffffff
    r1 = r1 ^ r3
    r3 = ror(r3, rot2)
    r3 = (r3 - r2) & 0xffffffff
    r2 = r2 ^ r0
    r0 = ror(r0, rot1)
    r0 = (r0 - r1) & 0xffffffff
    return r0, r1, r2, r3

def fwd_r4r5(r4, r5, xor_imm, rot):
    r4 = r4 ^ xor_imm
    r5 = (r5 + r4) & 0xffffffff
    r5 = rol(r5, rot)
    return r4, r5

def bwd_r4r5(r4, r5, xor_imm, rot):
    r5 = ror(r5, rot)
    r5 = (r5 - r4) & 0xffffffff
    r4 = r4 ^ xor_imm
    return r4, r5

def parse_bc_ops(bc):
    ops = []
    i = 0
    while i < len(bc):
        op = bc[i]
        if op == 0:
            ops.append(('NOP',))
            i += 1
        elif op == 1:
            dest = bc[i+1]; imm = struct.unpack_from('<I', bc, i+2)[0]
            ops.append(('SET_IMM', dest, imm))
            i += 6
        elif op in (2, 3, 4, 5, 6):
            dest = bc[i+1]; src = bc[i+2]
            name = {2: 'MOV', 3: 'ADD', 4: 'XOR', 5: 'AND', 6: 'OR'}[op]
            ops.append((name, dest, src))
            i += 3
        elif op in (7, 8):
            dest = bc[i+1]; sh = bc[i+2]
            name = {7: 'ROL', 8: 'SHR'}[op]
            ops.append((name, dest, sh))
            i += 3
        elif op in (9, 10, 11):
            dest = bc[i+1]; imm = struct.unpack_from('<I', bc, i+2)[0]
            name = {9: 'ADD_IMM', 10: 'XOR_IMM', 11: 'AND_IMM'}[op]
            ops.append((name, dest, imm))
            i += 6
        elif op == 12:
            dest = bc[i+1]; idx = bc[i+2]
            ops.append(('LOAD_IN', dest, idx))
            i += 3
        elif op == 13: ops.append(('GET_FLAG',)); i += 1
        elif op == 14: ops.append(('EMIT_FLAG',)); i += 1
        elif op == 15: ops.append(('HALT_ERR',)); i += 1
        else: ops.append(('UNKNOWN', op)); i += 1
    return ops

def solve(host='pwn.h7tex.com', port=42731):
    s = socket.create_connection((host, port), timeout=10)
    f = s.makefile('rw', buffering=1, encoding='ascii', newline='\n')
    f.readline() # banner
    f.readline() # commands

    f.write('GET\n')
    f.flush()
    raw_hex = f.readline().strip()
    data = bytes.fromhex(raw_hex)
    version, num_nodes, entry_node, nonce = struct.unpack('<HHHQ', data[4:18])
    offset = 18

    nodes = {}
    for i in range(num_nodes):
        node_id, branch_reg, branch_bit, default_target, bytecode_len = struct.unpack('<HBBHH', data[offset:offset+8])
        offset += 8
        bytecode = data[offset:offset+bytecode_len]
        offset += bytecode_len
        num_edges = data[offset]
        offset += 1
        edges = []
        for j in range(num_edges):
            cond, target_node, salt = struct.unpack('<BHI', data[offset:offset+7])
            edge_mac = data[offset+7:offset+13]
            offset += 13
            edges.append({'cond': cond, 'target': target_node, 'salt': salt, 'mac': edge_mac})
        nodes[node_id] = {
            'id': node_id,
            'branch_reg': branch_reg,
            'branch_bit': branch_bit,
            'default_target': default_target,
            'bytecode': bytecode,
            'edges': edges
        }

    # Verify edge authenticity using MINT
    valid_edges = {}
    for nid, n in nodes.items():
        valid_edges[nid] = []
        for e in n['edges']:
            edge_data = struct.pack('<HHBI', nid, e['target'], e['cond'], e['salt'])
            f.write(f"MINT {edge_data.hex()}\n")
            f.flush()
            resp = f.readline().strip()
            if e['mac'].hex() == resp:
                valid_edges[nid].append((e['cond'], e['target']))

    # Ladder walk
    curr = entry_node
    curr = valid_edges[curr][0][1] # entry -> round 0

    rounds = []
    for r in range(12):
        n = nodes[curr]
        ops = parse_bc_ops(n['bytecode'])
        rot1 = ops[1][2]
        rot2 = ops[4][2]
        imm1 = ops[6][2]
        imm2 = ops[7][2]

        ve = valid_edges[curr]
        t0 = [t for c, t in ve if c == 0][0]
        t1 = [t for c, t in ve if c == 1][0]

        ops0 = parse_bc_ops(nodes[t0]['bytecode'])
        ops1 = parse_bc_ops(nodes[t1]['bytecode'])
        xor0, rot_r5_0 = ops0[0][2], ops0[2][2]
        xor1, rot_r5_1 = ops1[0][2], ops1[2][2]

        rounds.append({
            'node': curr,
            'branch_reg': n['branch_reg'],
            'branch_bit': n['branch_bit'],
            'rot1': rot1,
            'rot2': rot2,
            'imm1': imm1,
            'imm2': imm2,
            't0': {'node': t0, 'xor': xor0, 'rot': rot_r5_0},
            't1': {'node': t1, 'xor': xor1, 'rot': rot_r5_1},
        })
        curr = valid_edges[t0][0][1]

    # Final check node
    final_node = nodes[curr]
    final_ops = parse_bc_ops(final_node['bytecode'])
    targets = {}
    for idx, op in enumerate(final_ops):
        if op[0] == 'XOR_IMM' and final_ops[idx-1][0] == 'MOV' and final_ops[idx-1][1] == 7:
            reg = final_ops[idx-1][2]
            targets[reg] = op[2]

    # Invert r0..r3
    r0, r1, r2, r3 = targets[0], targets[1], targets[2], targets[3]
    for r in reversed(rounds):
        r0, r1, r2, r3 = bwd_round(r0, r1, r2, r3, r['rot1'], r['rot2'], r['imm1'], r['imm2'])
    init_r0, init_r1, init_r2, init_r3 = r0, r1, r2, r3

    # Forward simulate r0..r3 to get exact branch decisions
    sim_r0, sim_r1, sim_r2, sim_r3 = init_r0, init_r1, init_r2, init_r3
    branch_choices = []
    for r in rounds:
        sim_r0, sim_r1, sim_r2, sim_r3 = fwd_round(sim_r0, sim_r1, sim_r2, sim_r3, r['rot1'], r['rot2'], r['imm1'], r['imm2'])
        regs = [sim_r0, sim_r1, sim_r2, sim_r3]
        bit_val = (regs[r['branch_reg']] >> r['branch_bit']) & 1
        branch_choices.append(bit_val)

    # Invert r4, r5 along selected branches
    r4, r5 = targets[4], targets[5]
    for r_idx in reversed(range(12)):
        choice = branch_choices[r_idx]
        b_info = rounds[r_idx]['t1' if choice == 1 else 't0']
        r4, r5 = bwd_r4r5(r4, r5, b_info['xor'], b_info['rot'])
    init_r4, init_r5 = r4, r5

    # Pack input and execute
    inp = struct.pack('<6I', init_r0, init_r1, init_r2, init_r3, init_r4, init_r5)
    f.write(f"RUN {inp.hex()}\n")
    f.flush()
    flag = f.readline().strip()
    s.close()
    return flag

if __name__ == '__main__':
    flag = solve()
    print(f"FLAG: {flag}")
