# CTF Workspace — Agent Rules

## Autonomy
- Run full ctf-solver triage before asking the user anything.
- Read-only local analysis never requires permission.
- Timebox: 3 failed approaches ⇒ switch technique (see skill escalation rule).

## Discipline
- Solver scripts → solutions/<challenge>/solve.py; must run end-to-end non-interactively.
- Every challenge gets solutions/<challenge>/NOTES.md with YAML frontmatter tags:
  `yaml
  ---
  challenge: <name>
  category: <web|crypto|rev|pwn|forensics|misc>
  techniques: [<technique1>, <technique2>]
  time_to_flag: <minutes>
  status: solved
  ---
  `
- Also output structured audit records into solutions/audit_log.jsonl per tool invocation.
- Verify before reporting: flag matches a known regex AND decodes to meaningful printable content.
- One challenge per subdirectory in challenges/ and solutions/; never pollute tools/.
- Continuous Learning & Memory: Consult TECHNIQUES_MEMORY.md at triage for matching patterns. After solving any challenge, append newly discovered techniques, formulas, or pitfalls into TECHNIQUES_MEMORY.md.

## Scope & Sandboxing
- Attack ONLY challenge infrastructure authorized in scope.yaml or explicit challenge parameters.
- Socket connections in helper scripts must route through the scope.validate_target(host, port) wrapper.
- Untrusted binaries default to running in WSL/isolated containers (docker run --network none -v ...:ro).
- No scanning, brute-forcing, or probing of unauthorized endpoints.

## User Resource & Question Focus
- Focus ONLY on the single, specific question provided by the user. Never attempt to solve, search for, or suggest answers to secondary questions, clipboard items, or background tasks.
- Restrict analysis STRICTLY to the resources and files explicitly provided or identified by the user for that challenge. Never search through browser history, unrelated downloads, or system folders for external materials unless explicitly directed.
- Dedicate 100% of reasoning and computational effort to solving the user-specified problem with the provided materials.

## Pre-Built Tool Suite & Execution Protocol
Any AI working in this workspace must use these pre-built deterministic tools rather than mental guessing or hallucination:
1. **Local RAG Writeup Database (1,650+ writeups & exploits):**
   - Command: `python tools/writeup_search.py "<keywords>" --code`
   - Use at Step 1 of triage to retrieve past solutions, exploit code blocks, and techniques.
2. **Recursive Multi-Layer Cipher Decoder:**
   - Command: `python tools/auto_decode.py "<ciphertext>" --xor`
   - Automatically cracks nested encodings (Hex, Base64/32/85, Binary, Decimal, URL, Morse, Bacon, ROT1-25, single-byte XOR).
3. **Hardware / Digital Logic Design (DLD):**
   - Command: `python tools/dld_solver.py`
   - Exact simulation for LFSRs, Berlekamp-Massey, Excess-3 (XS-3), Gray code, synchronous JK/D/T flip-flop counters.
4. **Esoteric Languages (Esolangs):**
   - Command: `python tools/esolang_solver.py <file_or_code>`
   - Deterministic execution of Brainfuck, Ook!, and Befunge-93 with step limiting.
5. **Constraint & Keygen Solver (Z3):**
   - Command: `python tools/z3_helper.py`
   - Automated SMT constraint solving for ASCII validation logic.
6. **Crypto Attack Suite:**
   - Script: `tools/crypto_toolkit.py` (Wiener, Fermat, small-e, Hastad, Common Modulus, DLP, Factordb).

