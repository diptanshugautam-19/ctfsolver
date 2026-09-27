---
challenge: countersign
category: rev
techniques: [arx-inversion, graph-walking, siphash-oracle]
time_to_flag: 15
status: solved
---

# Countersign — Solution Notes

## Overview
Countersign is an attestation core running an obfuscated virtual machine that executes a state transition graph. The service exposes four commands:
- `GET`: Streams the instance's program image as hex (including nodes, bytecode, and attested edge signatures).
- `NONCE`: Returns the instance's 64-bit nonce.
- `MINT <hex>`: Debug stamp oracle that computes a 6-byte SipHash-2-4 MAC over up to 16 bytes.
- `RUN <hex>`: Executes the core with a 24-byte input and prints the emitted output.

## Architecture & Analysis

### 1. Attestation Core Protocol & Graph Format
The program image streamed by `GET` starts with a header:
- `magic`: `"CSGN"` (4 bytes)
- `version`: `uint16` (2)
- `num_nodes`: `uint16` (40)
- `entry_node`: `uint16`
- `nonce`: `uint64`

Each node contains:
- `id`: `uint16`
- `branch_reg`: `uint8` (register to branch on, or `0xff` for unconditional)
- `branch_bit`: `uint8` (bit index in register)
- `default_target`: `uint16`
- `bytecode_len`: `uint16`
- `bytecode`: VM instructions
- `num_edges`: `uint8`
- `edges`: Array of 13-byte edges:
  - `cond`: `uint8` (expected branch bit value: 0, 1, or 255)
  - `target_node`: `uint16`
  - `salt`: `uint32`
  - `mac`: 6 bytes (SipHash-2-4 tag)

### 2. Edge Attestation & The MINT Oracle
Before transitioning between nodes, the core verifies that the edge has a valid 6-byte SipHash MAC computed over:
`src_node (2 bytes LE) || target_node (2 bytes LE) || cond (1 byte) || salt (4 bytes LE)`.

In the program image, dummy edges are included alongside authentic edges. The `MINT` command allows querying the SipHash tag of any data <= 16 bytes. By querying `MINT` for each candidate edge, we filter out all bogus edges and reveal the true graph topology.

### 3. Graph Structure: 12-Stage ARX Ladder
Filtering by valid MACs reveals a clean diamond/ladder DAG:
- **Entry Node (Round 0)**: Unpacks the 24-byte input into six 32-bit registers r0, r1, r2, r3, r4, r5.
- **12 ARX Rounds**:
  - Each round executes an ARX round exclusively on (r0, r1, r2, r3):
    r0 = (r0 + r1) <<< rot1
    r2 = r2 ^ r0
    r3 = (r3 + r2) <<< rot2
    r1 = r1 ^ r3
    r0 = r0 + imm1
    r2 = r2 ^ imm2
  - Then evaluates bit `branch_bit` of `branch_reg` (0 or 1).
  - Transitions to one of two intermediate nodes that modifies (r4, r5):
    r4 = r4 ^ imm_xor
    r5 = (r5 + r4) <<< rot_r5
  - Both intermediate nodes reconverge onto the next round node.
- **Final Node**: Checks (r0, r1, r2, r3, r4, r5) == (T0, T1, T2, T3, T4, T5). If equal, branches with `cond=0` to the flag emission node.

### 4. Mathematical Inversion
Because (r0, r1, r2, r3) is never modified by or dependent upon (r4, r5), each ARX round is directly invertible:
r2 = r2 ^ imm2
r0 = r0 - imm1
r1 = r1 ^ r3
r3 = (r3 >>> rot2) - r2
r2 = r2 ^ r0
r0 = (r0 >>> rot1) - r1

1. Starting from (T0, T1, T2, T3), we run the 12 rounds backward to recover the unique initial (r0, r1, r2, r3).
2. We simulate (r0, r1, r2, r3) forward to determine the exact branch decision (0 or 1) taken at every round.
3. With all 12 branch decisions known, the exact sequence of operations on (r4, r5) is fixed. We invert (r4, r5) backward from (T4, T5):
   r5 = (r5 >>> rot_r5) - r4
   r4 = r4 ^ imm_xor
4. Packing (r0, r1, r2, r3, r4, r5) into 24 bytes yields the input that navigates the core directly to the flag.

## Flag
`H7CTF{81d2ac39-bb56-43fe-9777-e16358efbb74}`
