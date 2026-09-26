---
challenge: ledger
category: pwn
techniques: [use-after-free, tcache-poisoning, safe-linking-bypass, got-overwrite]
time_to_flag: 8
status: solved
---

# Ledger — Pwn Solution Walkthrough

## 1. Challenge & Binary Overview
- **Binary:** `ledger` (x86-64 ELF, glibc 2.39 on Ubuntu 24.04).
- **Target Service:** `nc pwn.h7tex.com 42300`.
- **Protections:**
  - **Arch:** x86-64
  - **RELRO:** Partial RELRO (GOT is writable)
  - **Stack Canary:** Enabled
  - **NX:** Enabled
  - **PIE:** Disabled (`0x400000` base)

## 2. Vulnerability Discovery
1. **Uncalled "Win" Function (`audit` at `0x4012b6`):**
   - Reads `/flag` using `fopen` / `fgets` and outputs it via `printf("[audit] %s\n", buf)`.
2. **Use-After-Free (UAF) in `delete`:**
   - Option 2 (`delete`) calls `free(notes[idx])` but never clears `notes[idx] = NULL`.
   - Option 3 (`edit`) allows reading 80 bytes into `notes[idx]` if `notes[idx] != 0`.
   - Option 4 (`view`) writes out 80 bytes of `notes[idx]` if `notes[idx] != 0`.

## 3. Exploitation Path (glibc 2.39 Safe-Linking Bypass)
In glibc 2.39, tcache pointers are mangled with Safe-Linking:
$$P' = P \oplus (L \gg 12)$$
where $L$ is the address of the chunk's `fd` pointer.

1. **Heap Key Leak:**
   - Allocate chunk 0 and chunk 1 (size $0x50 \to 0x60$ chunk).
   - Free chunk 0, then free chunk 1 into tcache bin `0x60`.
   - Chunk 0 is the tail of the single-linked list, so its original `next == NULL`.
   - Its mangled `fd` is:
     $$0 \oplus (L_0 \gg 12) = L_0 \gg 12$$
   - Viewing chunk 0 via Option 4 directly leaks the Safe-Linking key $K = L_0 \gg 12$.
2. **Tcache Poisoning:**
   - Since chunk 0 and chunk 1 reside on the same heap page, $L_1 \gg 12 = L_0 \gg 12 = K$.
   - Target address: `0x404000` (which is 16-byte aligned and contains `free@GOT` and `puts@GOT`).
   - Edit chunk 1 to set its `fd` to:
     $$\text{mangled} = 0x404000 \oplus K$$
3. **Arbitrary Write & GOT Overwrite:**
   - Allocate chunk 2 to pop chunk 1 from tcache.
   - Allocate chunk 3 to pop `0x404000` from tcache.
   - Overwrite `puts@GOT` (`0x404008`) with `0x4012b6` (`audit`).
4. **Trigger:**
   - As soon as `add()` finishes, `main` loops back and `menu()` calls `puts()`.
   - Execution redirects into `audit()`, opening `/flag` and printing the clearance code.

## 4. Verified Flag
`H7CTF{560ec321-bb5f-4e99-9d05-7e48e00925e7}`
