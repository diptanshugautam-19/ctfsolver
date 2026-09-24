---
name: ctf-solver
description: >
  Autonomous CTF triage and solving methodology. Use for any capture-the-flag
  challenge across Web, Crypto, Rev, Pwn, and Forensics categories.
---

# CTF Solver Methodology

## Universal Triage & Dynamic Re-Triage Protocol

1. **Identify**: `file *` on all artifacts → `exiftool` → `binwalk` → `xxd | head` (magic bytes)
2. **Entropy**: `binwalk -E <file>` — >7.5 bits/byte ⇒ encrypted/compressed; <4 ⇒ plaintext/padding
3. **Flag hunt & Auto-Decode**:
   - `strings -n 6 <file> | python3 tools/flag_hunter.py --all-encodings`
   - For any suspicious string or multi-layer cipher: `python tools/auto_decode.py "<ciphertext>" --xor` (recursively unwraps Base64, Hex, Binary, Morse, Bacon, ROT, XOR).
4. **Classify & Route**: Dispatch to primary category playbook (Web, Crypto, Rev, Pwn, Forensics, DLD, Esolang).
5. **Local RAG & Memory Lookup**:
   - Query `python tools/writeup_search.py "<keywords>" --code` (searches 1,650+ indexed writeups & extracts exploit scripts).
   - Check `TECHNIQUES_MEMORY.md` to identify known challenge patterns, relevant scripts, and formulas.
6. **Deterministic Tool Execution**:
   - DLD / LFSR / Flip-Flops: `python tools/dld_solver.py`
   - Esolangs (Brainfuck / Ook / Befunge): `python tools/esolang_solver.py <file>`
   - Constraints / Keygens: `python tools/z3_helper.py`
7. **Continuous Artifact Re-Triage (Crucial for Hard/Multi-Stage CTFs)**:
   - *Rule:* Whenever any partial artifact is produced (e.g., extracted file from pcap/binary, decoded base64 string, leaked memory address, decompiled snippet), DO NOT assume you remain in the original playbook.
   - Immediately run Step 1, 3 & 6 on that new artifact. Route dynamically (e.g. Forensics -> Crypto -> Rev).
8. **Solve → Verify → Record**:
   - Flag must match a known regex AND decode to printable/meaningful content
   - Save `solutions/<challenge>/solve.py` (rerunnable end-to-end) + `flag.txt` + `NOTES.md` (with YAML frontmatter)

## Escalation Ladder (replaces flat retry counters)

Hard challenges intentionally resist trivial attacks. Follow the **4-Tier Escalation Ladder**:
1. **Tier 1: Heuristic & Direct Match**: Standard pattern scan, default credentials, simple strings, known CVE / fast signatures.
2. **Tier 2: Known Attack Library**: Dedicated algorithmic solvers (Wiener, Fermat, Håstad, SSTI polyglots, JWT confusion, format-string leak).
3. **Tier 3: Symbolic & Constrained Brute-Force**: Z3 SMT constraint modeling, bounded `angr` path exploration with library hook concretization, lattice reduction (LLL / Coppersmith), baby-step giant-step.
4. **Tier 4: Manual-Review / Deobfuscation Escalation**: Flag for human/expert review, extract CFG, run custom deobfuscation / VM opcode disassemblers.

## Flag Patterns (check in priority order)

| Priority | Pattern | Regex | Confidence Action |
|---|---|---|---|
| 1 | Generic | `(?i)(flag|ctf)\{[^}\s]{4,\}\}` | Auto-accept |
| 2 | Platform | `(picoCTF|HTB|THM|corctf|uiuctf|DUCTF|sun\{)\{?[^}]+\}` | Auto-accept |
| 3 | Base64 blob | `[A-Za-z0-9+/]{16,}={0,2}` | Decode, re-scan recursive (cap depth 5) |
| 4 | Hex blob | `(?:[0-9a-fA-F]{2}){12,}` | Decode, re-scan recursive (cap depth 5) |
| 5 | Broad braced | `[A-Za-z0-9_]{2,16}\{[!-~]{8,\}\}` | Scored candidate (entropy + printable ratio + keyword proximity) |

## Playbooks

### Web
- Recon: `robots.txt`, `sitemap.xml`, `/.git/` history extraction, backup files (`*.bak`, `~`, `.swp`), headers, cookies.
- Automated Probing: Use `tools/web_toolkit.py`:
  - SSTI polyglots (Jinja2, Twig, Freemarker, ERB, EJS).
  - JWT alg-confusion (`none`, `HS256` with public-key secret, empty secret).
  - LFI traversal (`php://filter/convert.base64-encode/resource=...`).
  - Blind SQLi and union injection points.

### Crypto
- Identification: Check parameters $(N, e, c)$, group structures $(g, h, p)$, classical cipher signatures.
- RSA / Factoring Ladder:
  - Small $e$ ($m^e < N$) $\to$ Integer root.
  - Close primes $\to$ **Fermat Factorization**.
  - Small $d$ ($d < \frac{1}{3}N^{1/4}$) $\to$ **Wiener's Attack**.
  - Multiple messages with same $m$ $\to$ **Håstad's CRT Broadcast** or **Common Modulus**.
  - Partial key/message exposure $\to$ **Coppersmith's Method / LLL**.
  - Factor database lookup $\to$ **factordb**.
- DLP: Small order subgroups $\to$ **Pohlig-Hellman** / **Baby-Step Giant-Step** (`tools/crypto_toolkit.py`).
- XOR: Single-byte English frequency scoring with unprintable byte penalty, multi-byte hamming distance.

### Reverse
- Identification: `file` $\to$ `checksec` $\to$ detect packer (`upx -d`) $\to$ architecture/language:
  - Python $\to$ `pycdc` / `uncompyle6`
  - Java / Android $\to$ `jadx`
  - .NET $\to$ `ilspycmd`
  - Native ELF/PE $\to$ Ghidra headless / IDA
- Symbolic Execution: For complex check functions, scaffold Z3 or bounded `angr` with concretized external calls to prevent state explosion.
- Obfuscation: Detect control-flow flattening / dispatcher loops; trace basic block execution dynamically.

### Pwn
- Mitigations: `checksec` (NX, Canary, PIE, RELRO).
- Automated Chains:
  - Cyclic pattern offset discovery (`tools/rev_pwn_helper.py`).
  - Gadget discovery via `ropper` or Pwntools `ROP(elf)`.
  - Libc offset resolution & `one_gadget` selection.
  - Heap primitives: Tcache poisoning, fastbin dup, House-of-* techniques.

### Forensics
- Images: `exiftool`, `zsteg` (PNG/BMP), `steghide` (JPG), audio spectrogram analysis.
- Network: `tools/pcap_helper.py` stream reassembly & HTTP decompression $\to$ dynamic re-triage of all carved files.
- Memory: Volatility3 plugin chaining (`windows.pslist`, `windows.filescan`, `windows.dumpfiles`).
- Git: Repository log/reflog recovery for committed secrets.
