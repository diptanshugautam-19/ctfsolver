---
challenge: sample_rev_keygen
category: rev
techniques: [SMT-Constraint-Solving, Z3, Static-Analysis, Validation-Extraction]
time_to_flag: 1
status: solved
---

# Vault Guardian — Solution Notes

## Challenge Overview
- **Category:** Reverse Engineering / Keygen
- **Binary/Script:** `challenges/sample_rev_keygen/vault.py`
- **Objective:** Recover the 16-character body of the flag `flag{...}` satisfying algebraic, XOR, and prefix constraints.

## Triage & Analysis
1. Inspected `vault.py`:
   - Enforces flag format `flag{<16 chars>}`.
   - Body characters must satisfy 10 mathematical relations:
     - `sum(b) == 1458`
     - Substring constraints: `body[0:4] == "z3_s"`, `body[8:12] == "k3y_"`
     - Bitwise XOR constraints: `(b[0] ^ b[1]) == 0x49`, `(b[4] ^ b[5]) == 0x46`, `(b[8] ^ b[9]) == 0x58`, `(b[12] ^ b[13]) == 0x07`
     - Arithmetic constraints: `b[2] + b[3] == 210`, `b[6]*3 - b[7] == 210`, `b[10] + b[11]*2 == 311`, `b[14] + b[15] == 82`

## Solution Strategy
- Rather than manually solving the non-linear simultaneous equations, modeled all characters as 16-bit integers (`BitVec`) in Z3 with standard printable ASCII ranges.
- Formulated the exact SMT constraints and solved.
- Solver returned satisfiable model in under 50ms.

## Result
- **Flag:** `flag{z3_s0vlrk3y_vq1!}`
- **Verification:** Passed `vault.check_flag()` check with `True`.
