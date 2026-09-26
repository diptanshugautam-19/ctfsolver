---
challenge: manifest
category: pwn
techniques: [format-string, arbitrary-write, bss-variable-overwrite, glibc-2.39]
time_to_flag: 3
status: solved
---

# Sparrow Freight Manifest — Format String Arbitrary Write Writeup

## 1. Challenge Overview
- **Binary:** `manifest` (64-bit ELF, x86-64, dynamically linked)
- **Target OS:** Ubuntu 24.04 LTS (`glibc 2.39`)
- **Remote Host:** `nc pwn.h7tex.com 42332`
- **Provided Files:**
  - `manifest`: Challenge binary
  - `libc.so.6`: Target system C library
  - `ld-linux-x86-64.so.2`: Matching dynamic linker
  - `README.txt`: Deployment information

## 2. Binary Mitigation Audit (checksec)
- **Arch:** x86-64 Little Endian (`ET_EXEC`)
- **PIE:** Disabled (static code/data addresses, load base `0x400000`)
- **Stack Canary:** Disabled
- **NX:** Enabled
- **RELRO:** Partial RELRO

## 3. Vulnerability Analysis
- The program displays an interactive menu in `main()` (`0x401363`):
  1. `leave feedback`: calls `feedback()` (`0x4012d9`)
  2. `view manifest`: calls `view_manifest()` (`0x401236`)
  3. `exit`
- In `feedback()`:
  - Reads up to 199 bytes into a stack buffer via `read(0, buf, 199)`.
  - Executes:
    ```c
    printf("You said: ");
    printf(buf); // Direct format string vulnerability!
    ```
- In `view_manifest()`:
  - Reads global variable `is_admin` located in `.bss` at `0x40407c`:
    ```c
    if (is_admin != 0) {
        FILE *f = fopen("/flag", "r");
        fgets(flag, sizeof(flag), f);
        printf("[manifest] clearance code: %s\n", flag);
    } else {
        puts("[!] admin clearance required.");
    }
    ```

## 4. Exploitation Strategy
Because Position Independent Executable (PIE) is disabled, the address of `is_admin` is statically fixed at `0x40407c`. We use the format string vulnerability to write a non-zero integer into `is_admin` via `%n`.

### Offset Discovery
- On x86-64 System V ABI, the first 5 format parameters are passed in registers (`RSI`, `RDX`, `RCX`, `R8`, `R9`).
- The 6th parameter (`%6$...`) corresponds to the top of the stack (`RSP`), which is precisely the start of our input buffer `buf`.

### Memory Layout & Alignment
Because `0x000000000040407c` contains leading null bytes (`0x00`), placing the address at the beginning of the format string would cause `printf` to stop parsing prematurely.
Instead, we place the format specifier first and append the 64-bit target address:
- **Bytes 0..7 (Offset 6):** `b"%1337c%8"`
- **Bytes 8..15 (Offset 7):** `b"$nAAAAAA"`
  (Combined bytes 0..15: `b"%1337c%8$n".ljust(16, b"A")`)
- **Bytes 16..23 (Offset 8):** `p64(0x40407c)` (target pointer to `is_admin`)

When executed:
1. `%1337c` outputs 1,337 padding spaces.
2. `%8$n` writes the count (1,337) into the memory location pointed to by argument 8 (`0x40407c`).
3. Global variable `is_admin` becomes `1337` (`!= 0`).
4. In the menu loop, send option `2` (`view manifest`).
5. `view_manifest()` passes the check and outputs the flag.

## 5. Retrieved Flag
```text
H7CTF{b13f2a35-7d89-4612-9a77-a63a3ed08d33}
```
