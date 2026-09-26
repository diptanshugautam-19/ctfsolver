---
challenge: kintsugi_vault
category: rev
techniques: [spn_cipher_inversion, ed25519_seed_recovery, dynamic_bytecode_template_reconstruction]
time_to_flag: 45
status: solved
flag: "H7CTF{9bad456f-6908-413e-bfa8-5fb33a7bcdf3}"
---

# Kintsugi Vault — Solution Notes

## Overview
The Kintsugi Vault challenge provides an offline static binary runtime (`vmrun`), guardian agent shard files (`*.shard`), a 32-byte instance public attestation key (`pubkey.bin`), and an attestation web endpoint at `/attest`.

## Architecture & Reversing Findings

### 1. Shard Structure
Each shard binary consists of:
- `0x00`: Magic `KSHD`
- `0x04`: Version (1)
- `0x05`: Flags (`0x01` = Start Shard, `0x02` = Terminal Shard, `0x00` = Normal)
- `0x06`: Key length (8 bytes)
- `0x08`: Decode table length (256 bytes)
- `0x0a`: Program length (649 bytes)
- `0x0e`: Content ID (16 bytes, matching shard filename)
- `0x1e`: CRC32 of valid decode table (4 bytes) + next chain link pointer (16 bytes)
- `0x32`: Payload region (256 bytes)
- `0x132`: SBOX table (256-byte bijective permutation)
- `0x232`: Bytecode program (649 bytes)

### 2. VM Semantics & Opcode Recovery
Disassembly of `vmrun` revealed a 14-entry signed relative jump table:
- Op 1: `LOADK r[a], key[b]` (3B)
- Op 2: `LOAD r[a], imm32` (6B)
- Op 3: `SWAP r[a], r[b]` (3B)
- Op 4: `XOR r[a], r[b]` (3B)
- Op 5: `ADD r[a], r[b]` (3B)
- Op 6: `IMUL r[a] *= r[b]` (3B)
- Op 7: `AND r[a], r[b]` (3B)
- Op 8: `OR r[a], r[b]` (3B)
- Op 9: `ROL r[a], imm8` (3B)
- Op 10: `SBOX r[a] = sbox[r[b] & 0xFF]` (3B)
- Op 11: `CMP r[a], imm32` (6B)
- Op 12: `ANDI r[a], imm32` (6B)
- Op 13: `XORI r[a], imm32` (6B)

### 3. Agent Shard Classification
Across instances, the guardian agent shards split into two distinct categories:
- **Chain Agents (4 shards):**
  - Start (`flags=1`)
  - Intermediate 1 (`flags=0`, degenerate decode table)
  - Intermediate 2 (`flags=0`, degenerate decode table)
  - Terminal (`flags=2`)
  Structure: 3 rounds of SPN (Substitution-Permutation Network) over 8 registers with bijective SBOXes, 16 linear XOR mixing operations, and immediate masking before the final `CMP` assertions.
- **Decoy Agents (3 shards):**
  - Degenerate structure with single SBOX round followed by arithmetic mixing and 32-bit registers. Not part of the 4-shard custody chain.

### 4. Mathematical Seed Inversion
Running the 3-round SPN cipher backwards from the final `CMP` registers:
1. Invert Round 3 XOR immediates and 16-operation linear mixing.
2. Invert SBOX via lookup table inverse.
3. Invert Round 2 XOR immediates and linear mixing.
4. Invert Round 1 XOR immediates and linear mixing.
5. Invert input masking (`ANDI`/`XORI`) yielding:
   - Start shard: 16 candidate keys
   - Intermediate 1: 32 candidate keys
   - Intermediate 2: 32 candidate keys
   - Terminal: 64 candidate keys

### 5. Instance Handout Synchronization & Seed Recovery
Instances dynamically generate their own instance keypair and shards. Downloading `/handout.tar.gz` directly from the live challenge web endpoint yields the exact, synchronized shard suite and target `pubkey.bin`.
- Target Instance: `https://web-986d60e27fd022f4.web.h7tex.com`
- Target Public Key: `4c511cf08ecb25a5781c14f9c0bc30aaca12d484e9913e2ca0e554bd1946bc87`
- Shard Order: `af33c70a` -> `b8e17d89` -> `0f891f8d` -> `eeea1242`
- Recovered 32-Byte Custody Seed: `32fceb4581742dafecea7a61fa2bdfc1c4a0df2b6457bbf28cf750e2006e54c7`

### 6. Attestation & Flag Retrieval
The automated solver (`solutions/kintsugi_vault/solve.py`):
1. Downloads and unpacks the live instance's `/handout.tar.gz`.
2. Dynamically maps VM opcodes from the canonical bytecode templates.
3. Inverts the 3-round SPN cipher across all chain shards.
4. Derives and identifies the unique 32-byte Ed25519 custody seed matching `pubkey.bin`.
5. Requests a live challenge nonce from `GET /attest`.
6. Signs the nonce using the Ed25519 custody seed and submits `POST /attest` with `{"nonce": nonce, "sig": sig}`.
7. Successfully authenticates the attestation and recovers the flag:
   `H7CTF{9bad456f-6908-413e-bfa8-5fb33a7bcdf3}`
