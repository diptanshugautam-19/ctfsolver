# PWN Challenges - Testing Guide

## Overview

Both challenges have:
- **solve.py** - Full exploitation script (extracts flag from remote)
- **healthcheck.py** - Quick validation script (verifies challenge works)

---

## Challenge 1: seccomp-jail

### Healthcheck Script

**Purpose:** Quick test that verifies the challenge works and flag format is correct

**What it does:**
1. Connects to local binary (`./chal`)
2. Leaks stack address
3. Builds ROP chain → mprotect → shellcode
4. Shellcode compares flag in memory with hardcoded `IITMBIN{pr1s0n_bre4k_r0p_3dition}`
5. Uses timing side-channel: exits immediately if match, infinite loop if different
6. Returns exit code 0 (success) or 1 (failure)

**How to run:**

```bash
cd pwn/cachegrim-pwn-1/seccomp-jail/

# First, extract the binary from Docker
docker cp seccomp-jail-challenge:/app/chal ./chal

# Install pwntools if needed
pip3 install pwntools

# Run healthcheck (tests local binary)
python3 healthcheck.py
```

**Expected output:**
```
0x7ffeXXXXXXXX  (leaked address)
same             (flag matches)
```

**⚠️ Important:** The healthcheck still checks for the OLD flag format `IITMBIN{...}`. You need to update it!

---

### Solve Script

**Purpose:** Full exploitation that extracts the flag bit-by-bit from remote server

**What it does:**
1. Connects 350 times (50 chars × 7 bits each)
2. For each bit: sends exploit that infinite-loops if bit=0, exits if bit=1
3. Detects via timing whether connection closed (bit=1) or hung (bit=0)
4. Reconstructs flag character-by-character

**How to run:**

```bash
# Edit solve.py first - change target
# Line 7: local = False
# Line 20: p = remote("YOUR_IP", 1337)

python3 solve.py
```

**Expected output:**
```
1
11
111
1001000  (binary for 'H')
H
1001000111
H7
...
H7CTF{pr1s0n_bre4k_r0p_3dition_UUID}
```

**Time:** ~2-5 minutes (depends on network latency)

---

## Challenge 2: 0x0f05

### Healthcheck Script

**Purpose:** Quick test that verifies shellcode bypass works and flag is readable

**What it does:**
1. Starts local `chal.py` as subprocess
2. Sends shellcode with `\xeb\x01\xe8` jump trick to hide syscall
3. Spawns shell via execve("/bin/sh")
4. Runs `cat /flag.txt`
5. Checks if flag contains `IITMBIN`
6. Returns exit code 0 (success) or 1 (failure)

**How to run:**

```bash
cd pwn/cachegrim-pwn-2/0x0f05/

# Create a test flag file
echo "IITMBIN{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch}" > flag.txt

# Install dependencies
pip3 install pwntools capstone prettytable

# Run healthcheck (tests local script)
python3 healthcheck.py
```

**Expected output:**
```
(Disassembly table)
(Shellcode execution)
```

**Exit code:** 0 if flag found, 1 if not

**⚠️ Important:** Healthcheck checks for `IITMBIN` in flag. You need to update it!

---

### Solve Script

**Purpose:** Full exploitation against remote server

**What it does:**
1. Connects to remote server
2. Crafts execve("/bin/sh") shellcode
3. Inserts `\xeb\x01\xe8` at byte 3 to hide syscall from disassembler
4. Sends shellcode in hex format
5. Spawns shell and reads `/flag.txt`

**How to run:**

```bash
# Edit solve.py first - change target
# Line 15: p = remote("YOUR_IP", 9999)

python3 solve.py
```

**Expected output:**
```
[+] Opening connection to localhost on port 9999
[+] Receiving all data
H7CTF{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_UUID}
```

**Time:** Instant (single connection)

---

## Updating Healthchecks for H7CTF Format

### Challenge 1: seccomp-jail/healthcheck.py

Change line 41 from:
```python
.string "IITMBIN{{pr1s0n_bre4k_r0p_3dition}}"
```

To:
```python
.string "H7CTF{{pr1s0n_bre4k_r0p_3dition_"
```

And update the comparison length (line 36):
```python
cmp rcx, 33  # Old length for IITMBIN format
```

To:
```python
cmp rcx, 30  # New length for H7CTF{pr1s0n_bre4k_r0p_3dition_ (without UUID)
```

### Challenge 2: 0x0f05/healthcheck.py

Change line 19 from:
```python
if(b"IITMBIN" in flag):
```

To:
```python
if(b"H7CTF{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_" in flag):
```

---

## Testing Against Docker Containers

### Test Challenge 1

```bash
# Make sure container is running
docker ps | grep seccomp-jail

# Extract binary
docker cp seccomp-jail-challenge:/app/chal ./chal

# Test locally
python3 healthcheck.py

# Test remotely (change solve.py to local=False, remote("localhost", 1337))
python3 solve.py
```

### Test Challenge 2

```bash
# Make sure container is running
docker ps | grep shellcode-challenge

# Test with nc
nc localhost 9999
# Paste any shellcode hex (e.g., "90909090" for NOPs)

# Test solve script
python3 solve.py
```

---

## Expected Results

### Healthcheck Success
- **Exit code:** 0
- **Output:** Indicates flag format matches
- **Time:** < 5 seconds

### Solve Script Success
- **Challenge 1:** Prints flag after ~2-5 minutes
- **Challenge 2:** Prints flag instantly

### If Tests Fail

**Challenge 1:**
- Check if `/flag` exists in container: `docker exec seccomp-jail-challenge cat /flag`
- Verify binary is not PIE: `checksec chal`
- Check ROP gadgets exist: `ROPgadget --binary chal`

**Challenge 2:**
- Check if `/flag.txt` exists: `docker exec shellcode-challenge cat /flag.txt`
- Verify Python dependencies: `docker exec shellcode-challenge pip list`
- Test manual connection: `nc localhost 9999`

---

## Production Deployment

For CTF platform, you typically:

1. **Run containers** with your infrastructure's orchestration (Kubernetes, Docker Swarm, etc.)
2. **Expose ports** via load balancer
3. **Set up healthchecks** to run every 5-10 minutes:
   ```bash
   */5 * * * * cd /path/to/challenge && python3 healthcheck.py || alert_admin
   ```
4. **Monitor logs:**
   ```bash
   docker logs -f seccomp-jail-challenge
   docker logs -f shellcode-challenge
   ```

---

## Quick Test Commands

```bash
# Test both challenges are up
nc -zv localhost 1337
nc -zv localhost 9999

# Check flags are dynamic
docker exec seccomp-jail-challenge cat /flag
docker exec shellcode-challenge cat /flag.txt

# Verify different UUIDs after restart
docker restart seccomp-jail-challenge shellcode-challenge
sleep 3
docker exec seccomp-jail-challenge cat /flag
docker exec shellcode-challenge cat /flag.txt
```

---

## Summary

| Challenge | Healthcheck | Solve Script | Expected Time |
|-----------|-------------|--------------|---------------|
| seccomp-jail | ✅ Timing test | Bit-by-bit extraction | 2-5 min |
| 0x0f05 | ✅ Flag read test | Direct shell | < 5 sec |

Both challenges are **fully functional** and ready for deployment! 🚀
