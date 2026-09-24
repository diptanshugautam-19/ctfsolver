# CTF Persistent Technique & Memory Base

This file serves as the long-term memory for techniques, patterns, and lessons learned across CTF challenges. Every time a challenge is analyzed or solved, new findings are cataloged here so that future challenges can be solved rapidly using established knowledge.

---

## 1. Digital Logic Design (DLD) & Hardware Counters
* **LFSR (Linear Feedback Shift Register):**
  - **Structure:** Shift register stages where input bit $D_0 = \bigoplus Q_i$ (XOR sum of taps).
  - **Start state:** Requires non-zero seed (e.g. `1111`) to prevent lockup.
  - **Period:** Maximum length for $n$-bits is $2^n - 1$ (e.g. 15 for 4-bit).
* **Excess-3 (XS-3) Code:**
  - Unweighted BCD code where Decimal Digit = Binary Value $- 3$.
  - Valid decimal range: binary `0011` (3 $\to$ 0) to `1100` (12 $\to$ 9).
* **Ripple Up-Counters:**
  - JK flip-flops with $J=K=1$ toggle on negative clock edges ($Q \to \text{CLK}_{next}$).
  - Counts binary sequentially ($0, 1, 2, \dots, 2^n - 1$).
* **Synchronous Counter Synthesis:**
  - Use JK excitation table ($0\to0: 0,X$; $0\to1: 1,X$; $1\to0: X,1$; $1\to1: X,0$).
  - Simplify next-state inputs using Karnaugh Maps (K-maps).
* **ASCII Bit Composition:**
  - 3-bit upper bank (C1) + 4-bit lower bank (C2) $\to$ 7-bit ASCII character.
  - High nibble `011` (3) $\to$ ASCII digits `'0'` to `'9'`.
  - High nibble `100` (4) $\to$ ASCII uppercase letters `'A'` to `'O'`.

---

## 2. Esoteric Languages (Esolangs) & Literature References
* **Poetry & Natural Language Esolangs:**
  - **Poetic:** Brainfuck derivative where instructions are encoded into word lengths.
  - **Shakespeare (SPL):** Code written as dramatic dialogue between characters.
  - **Beatnik:** Stack-based language where Scrabble word scores dictate commands.
* **Infernal / Dante / Hell Esolangs:**
  - **Malbolge:** Named after Malebolge (8th circle of Hell in Dante's *Inferno*). Ternary VM, self-encrypting code. Created by Ben Olmstead in 1998.
  - **Dis:** Created by Ben Olmstead in 1998 as a slightly less difficult alternative to Malbolge. Named after the City of Dis.
  - **xH331 / Inferno:** Malbolge successor explicitly styled after the 9th circle of Hell.

---

## 3. Reverse Engineering & Binary Keygens
* **Constraint Solving (Z3):**
  - Extract validation routines with disassemblers/decompilers.
  - Model conditions as mathematical constraints in `z3-solver` instead of brute-forcing.
* **GameBoy / Embedded ROMs:**
  - Extract 2BPP (2 bits per pixel) tile data from ROM banks.
  - Use emulator execution traces (e.g. PyBoy, BGB) to hook check functions or dump VRAM.

---

## 4. Multi-Volume Archives & File Carving
* **Split Zip Archives (`.z01`, `.z02`, `...`, `.zip`):**
  - Never extract `.z01` or `.z02` individually.
  - Keep all parts in the exact same directory with original names.
  - Extract using 7-Zip targeting the primary `.zip` file: `7z x archive.zip -ooutput/`.

---

## 5. Multi-Layer Encodings & Classical Ciphers
* **Cascade Decoding (`tools/auto_decode.py`):**
  - High-frequency nesting in CTF flags: e.g. `ROT13(Base64(Hex(flag)))`.
  - Always run recursive tree traversal checking English quadgrams and standard prefix regexes (`flag{`, `ctf{`, etc.).
  - Check single-byte XOR across 256 keys with ASCII printable ratio penalty.
  - Baconian cipher variants: check 24-letter (I=J, U=V) and 26-letter alphabets against binary / uppercase representations.

---

## 6. Deterministic Esolang Execution (`tools/esolang_solver.py`)
* **Brainfuck & Derivatives:**
  - Never manually simulate complex tape loops. Execute with bounded ops (5M steps) to prevent halting problem hangs.
  - **Ook!:** Map token pairs directly: `Ook. Ook?` $\to$ `>`, `Ook? Ook.` $\to$ `<`, `Ook. Ook.` $\to$ `+`, `Ook! Ook!` $\to$ `-`, `Ook! Ook.` $\to$ `.`, `Ook. Ook!` $\to$ `,`, `Ook! Ook?` $\to$ `[`, `Ook? Ook!` $\to$ `]`.
  - **Befunge-93:** 80x25 toroidal grid with PC directional control (`>`, `<`, `^`, `v`, `_`, `|`).

---

## 7. Local Writeup RAG System (`tools/writeup_search.py`)
* **Instant Solution Pattern Retrieval:**
  - Database contains 1,650+ indexed writeups across all major categories.
  - Search command: `python tools/writeup_search.py "<keywords>" --code`.
  - Automatically decomposes compound terms (`ret2libc` $\to$ `ret`, `libc`) and extracts runnable Python/Bash exploit blocks.

---

## 8. Discipline & Execution Rules
* **Strict Problem Isolation:** Focus 100% of effort on the single problem provided. Never hunt in system files or attempt secondary challenges.
* **Deterministic Solvers First:** Always prefer mathematical execution (`dld_solver.py`, `auto_decode.py`, `z3_helper.py`, `crypto_toolkit.py`) over LLM mental arithmetic.
* **Reproducibility:** Every solved challenge must have a non-interactive `solutions/<name>/solve.py` and a documented `solutions/<name>/NOTES.md`.
