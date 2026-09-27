# Deep Analysis: Hothouse Cellular-Automaton Coprocessor

---
challenge: hothouse
category: rev/pwn
techniques: [cellular-automata, gf2-linear-algebra, nullspace-projection, seccomp-orw]
status: analyzed
---

## 1. Executive Summary & Binary Specifications

- **Target Binary:** `hothouse/hothouse`
- **Format:** ELF 64-bit LSB executable, x86-64, statically linked, stripped.
- **Protocol Service:** Line-based text protocol communicating over `stdin`/`stdout` (`nc pwn.h7tex.com 40196`).
- **Memory Architecture:**
  - `mmap(NULL, 0x2000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)` allocates two pages (`0x2000` bytes).
  - **Page 0 (`[entry - 0x1000]`):** Stores the target path (e.g. `/flag_...`) at a pseudo-random offset in `[0x40, 0xf80]`. All preceding bytes are `0x00`.
  - **Page 1 (`[entry]`):** Re-protected to `PROT_READ | PROT_WRITE | PROT_EXEC`. Holds the 128-byte settled fabric and is called directly upon `FIRE`.

---

## 2. Command Protocol & Budget Limits

| Command | Arguments | Budget | Description |
| :--- | :--- | :--- | :--- |
| `SEED` | `r c` | 4,096 | Sets `seed[r * 32 + c] = 1`. Coordinates must satisfy $0 \le r, c < 32$. |
| `INCUBATE` | *none* | 64 | Copies `seed` to stack and evolves the CA for 7 generations against `substrate`. Slices 32×32 bits into the 128-byte Page 1 buffer. |
| `PROBE` | `r c` | 20,000 | Returns the byte value at `fabric[r * 4 + (c >> 3)]`. |
| `RENDER` | *none* | $\infty$ | Prints the 32×32 settled fabric row by row (`#` for 1, `.` for 0). |
| `FIRE` | *none* | 1 | Installs seccomp filter, transfers execution to Page 1 via `call [page_1]`. |

---

## 3. Cellular Automaton Mechanics (Hexagonal GF(2) Linear Map)

- **Neighborhood:** 6 hexagonal neighbor offsets:
  $$\mathcal{N} = \{(-1, 0), (1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)\}$$
- **State Vector:** $x \in \mathbb{F}_2^{1024}$, where cell $(r, c)$ maps to index $i = r \times 32 + c$.
- **Evolution Step:**
  $$x_{t+1} = M x_t \oplus B$$
  where $M \in \mathbb{F}_2^{1024 \times 1024}$ is the adjacency matrix, and $B \in \mathbb{F}_2^{1024}$ is the immutable substrate generated at startup.
- **7-Generation Closed Form:**
  $$x_7 = M^7 x_0 \oplus C \quad \text{where } C = \sum_{k=0}^{6} M^k B$$
- **Leakage Vector ($C$):**
  Since $x_0 = \mathbf{0}$ upon connection initialization, running `INCUBATE` followed immediately by `RENDER` yields:
  $$x_7 = M^7 (\mathbf{0}) \oplus C = C$$

---

## 4. Rank Analysis & The 32-Dimensional Parity Constraint

Gaussian elimination over $\mathbb{F}_2$ establishes:
$$\text{rank}(M) = 992, \quad \text{rank}(M^7) = 992 \implies \dim(\ker((M^7)^T)) = 32$$

A target bitfield $T \in \mathbb{F}_2^{1024}$ is reachable if and only if the difference vector $\Delta = T \oplus C$ resides in the column space of $M^7$:
$$V (T \oplus C) = \mathbf{0} \pmod 2 \iff V T = V C \pmod 2$$
where $V \in \mathbb{F}_2^{32 \times 1024}$ is the matrix whose rows form a basis of $\ker((M^7)^T)$.

### Guaranteed Reachability via Padding Bits
- Analyzing the submatrix of $V$ restricted to the upper half of the fabric (bytes 64 to 127) confirms:
  $$\text{rank}\left(V_{[:, \text{bytes 64..127}]}\right) = 32 \quad (\text{Full Rank})$$
- **Result:** Any arbitrary prefix of up to 64 bytes placed in bytes 0..63 is **100% reachable**. The 32 parity constraints can always be satisfied by adjusting bits in the padding region (bytes 64..127).

---

## 5. End-to-End Resolution Pipeline

```
1. Connect to service (pwn.h7tex.com:40196)
   │
2. Send INCUBATE with seed = 0
   │
3. Send RENDER to read 32x32 characters -> Parse binary vector C
   │
4. Define target prefix T[0..63] (ORW machine code sequence)
   │
5. Solve linear sub-system: V_pad * delta_pad = (V * C) ^ (V * T)  (mod 2)
   T[pad_indices] ^= delta_pad
   │
6. Solve full linear system: M^7 * x0 = T ^ C  (mod 2)
   │
7. Send SEED r c for each cell where x0[r, c] == 1 (~500 commands)
   │
8. Send INCUBATE (settles T exactly into Page 1)
   │
9. Send FIRE (triggers seccomp + executes Page 1)
```

---

## 6. Register State & Execution Context on FIRE

When execution enters Page 1 at `0x40365c`:
- **`RIP`:** Points to the start of Page 1.
- **Page 0 Offset:** Page 0 resides exactly at `[RIP - 0x1000]`.
- **`r14`:** Retains the exact byte offset of the flag path inside Page 0 (`[0x40, 0xf80]`).
- **Seccomp Whitelist:** Only `openat` (257), `read` (0), `write` (1), `mmap` (9), `exit` (60), `exit_group` (231) are permitted.
