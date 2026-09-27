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
  - Database contains **4,240+ indexed writeups, exploit scripts, contracts, and hardware sources** across all major categories (Hardware, Pwn, Web, Crypto, Rev, Forensics, Web3/Blockchain).
  - Supported extensions: `.md`, `.txt`, `.rst`, `.py`, `.sh`, `.sol`, `.pdf`, `.ino`, `.c`, `.cpp`, `.h`, `.v`, `.sv`, `.vhd`.
  - Search command: `python tools/writeup_search.py "<keywords>" --code`.
  - Automatically decomposes compound terms (`ret2libc` $\to$ `ret`, `libc`) and extracts runnable Python, Bash, and Solidity exploit blocks.

---

## 8. Web3 & Smart Contract Security (EVM / Solidity / Vyper)
* **Foundry Automated Exploit Framework:**
  - Standard solution pattern: Write attack contracts in `script/` or `test/` and run `forge test --match-contract <ExploitTest> -vvvv`.
* **Common Attack Primitives:**
  - **Reentrancy:** State updates after external `.call{value: ...}("")`. Mitigate with Checks-Effects-Interactions (CEI) or ReentrancyGuard.
  - **`delegatecall` Storage Collisions:** Code executes in caller context; storage slot 0 in logic contract overwrites slot 0 (often `owner`) in proxy contract.
  - **Force-Feeding Ether:** `selfdestruct(target)` bypasses `receive()` / `fallback()` functions, breaking contracts relying on `address(this).balance == X`.
  - **Read-Only Reentrancy & Virtual Price Manipulation (MirrorLend / Curve pattern):**
    - Occurs when a pool function (`removeLiquidity`) decreases `totalSupply` and sends ETH via `.call{value: ...}("")` *before* transferring out other ERC20 tokens.
    - During the intermediate callback, `token.balanceOf(pool)` is still high while `totalSupply` is already reduced, artificially spiking `get_virtual_price() = (balance + tokens) / totalSupply`.
    - Exploitation: Deposit small collateral into a lending protocol using that pool's `get_virtual_price()`, trigger `removeLiquidity()`, borrow the maximum inflated debt inside the `receive()` callback, and let the transaction finish. The final collateral value normalizes while `totalDebt` remains permanently higher, rendering the protocol undercollateralized.
  - **Compiler Bugs (Vyper / Solc):** Vyper `concat()` leading byte overwrite (CVE-2024-22419), ABI decoding dynamic array negative offset read (CVE-2024-26149).
  - **ERC-4626 First Depositor / Share Inflation Attack (GenesisVault pattern):**
    - Occurs when `convertToShares` calculates $\text{assets} \times \text{totalSupply} / \text{reserve}$ and integer division truncates to zero when $\text{assets} \times \text{totalSupply} < \text{reserve}$.
    - Exploit Flow:
      1. Attacker deposits 1 wei of assets when `totalSupply == 0`, receiving 1 wei of shares.
      2. Attacker transfers large donation $D$ directly to vault and calls `sync()` (updating `reserve = D + 1` while `totalSupply = 1`).
      3. Target victim deposits amount $D$. Vault calculates $\text{shares} = \lfloor D \times 1 / (D + 1) \rfloor = 0$. Victim receives 0 shares.
      4. Attacker redeems their 1 share via `redeem(1, ...)` and claims $\lfloor 1 \times (2D + 1) / 1 \rfloor = 2D + 1$, extracting all assets.
    - Mitigations: Virtual shares/offset (e.g. OpenZeppelin ERC4626 +1 share / +1 asset virtual offset) or permanently locking the initial $1000$ shares to `address(0)`.


---

## 9. Binary Exploitation & Reverse Engineering Tooling
* **Installed Python Frameworks:**
  - `pwntools`: Standard ELF, ROP, process/remote I/O, cyclic patterns, format-string solver.
  - `ptrlib`: Lightweight CTF library by ptr-yudai for fast binary/crypto interactions (`from ptrlib import *`).
* **IDA Pro Live MCP Server (`tools/pcm`):**
  - If IDA Pro is running locally, `tools/pcm` acts as a Model Context Protocol server connecting directly to Hex-Rays decompiler, basic block graphs, cross-references, and IDAPython REPL.
* **glibc 2.32+ Safe-Linking Tcache Poisoning & GOT Hijacking:**
  - Pointers in tcache are protected with safe-linking: $P' = P \oplus (L \gg 12)$, where $L$ is the pointer's memory location.
  - The tail of a tcache list points to `NULL`, so `tail->fd = 0 ^ (L_{tail} >> 12) = L_{tail} >> 12`.
  - A UAF read on the tail chunk immediately leaks the safe-linking key $K = L \gg 12$.
  - To poison a chunk on the same heap page to point to an arbitrary 16-byte aligned address $T$, write $T \oplus K$ into its `fd`.
  - In binaries with No PIE and Partial RELRO, $T$ can directly target the Global Offset Table (e.g. `0x404000`), allowing immediate overwrite of PLT stubs (`puts@GOT`, `free@GOT`) with existing win functions (`audit()`).


---

## 10. Discipline & Execution Rules
* **Strict Problem Isolation:** Focus 100% of effort on the single problem provided. Never hunt in system files or attempt secondary challenges.
* **Deterministic Solvers First:** Always prefer mathematical execution (`dld_solver.py`, `auto_decode.py`, `z3_helper.py`, `crypto_toolkit.py`) over LLM mental arithmetic.
* **Reproducibility:** Every solved challenge must have a non-interactive `solutions/<name>/solve.py` and a documented `solutions/<name>/NOTES.md`.

---

## 11. Hardware, IoT & Embedded Security
* **Serial & Bus Protocols:**
  - **UART:** Asynchronous serial (TX/RX, GND). Framing: Start bit (0), 5-9 data bits (usually 8 LSB-first), optional parity bit, 1-2 stop bits (1). Baud rate detection: measure shortest pulse width $\Delta t$, Baud $\approx 1/\Delta t$ (common: 9600, 19200, 38400, 57600, 115200).
    - *Raw Bitstream Parsing:* Idle line = 1. Transition 1 $\to$ 0 signals Start bit. Collect $N$ bits, reverse slice (`[::-1]` for LSB-first), verify parity (`sum(bits) % 2 == 0` for even), discard stop bit.
  - **I2C:** Synchronous 2-wire serial (SDA data, SCL clock, pull-up resistors). Addressing: 7-bit or 10-bit address + R/W bit (0=Write, 1=Read), followed by ACK (0) / NACK (1).
    - *Hardware Address Hijacking:* Slave address format (e.g. PCF8574 `0100[A2][A1][A0]`). If target IC has pull-up/down resistors on address lines, overpower the address pin using an attached module's GPIO to forcibly reassign the original chip's I2C ID, preventing slave address collisions when spoofing the bus device.
    - *4x4 Matrix Keypad Scanning (I2C I/O Expander):* MCU drives row scan `0xF0` (columns high, row pulled low `0xE0, 0xD0, 0xB0, 0x70`), then column scan `0x0F` (rows high, column pulled low `0x0E, 0x0D, 0x0B, 0x07`). Simulated keypress sends corresponding pattern pairs.
  - **SPI:** Synchronous 4-wire serial (MOSI, MISO, SCK, CS/SS active low). Clock polarity (CPOL) and phase (CPHA) determine sampling edges (Modes 0 to 3).
  - **JTAG / SWD:** IEEE 1149.1 test access port (TMS, TCK, TDI, TDO, TRST) and ARM Serial Wire Debug (SWDIO, SWCLK). Used for hardware debugging, boundary scans, reading device IDs (`IDCODE`), dumping internal flash/SRAM, and runtime memory patching.
  - **Wiegand Protocol:** Access control cards and keypads. 2-wire interface (DATA0 / Green, DATA1 / White). Falling edge on DATA0 = bit 0, DATA1 = bit 1. Formats: 26-bit standard (leading even parity, 8-bit facility code, 16-bit card ID, trailing odd parity), 4-bit / 8-bit BCD per keypress. Decode with PulseView / Sigrok or transition timestamp analysis.
  - **CAN Bus:** Differential signaling (CAN-H, CAN-L, 120$\Omega$ termination). 11-bit standard or 29-bit extended ID, RTR bit, DLC (0-8 bytes), CRC, ACK. Common tools: `can-utils` (`candump`, `cansend`, `canplayer`).
* **Logic Analyzers & Waveform Forensics:**
  - Tools: Saleae Logic 2 (`.sal`), Sigrok / PulseView (`.sr`, `.vcd`, `.csv`).
  - Waveform parsing: Convert VCD (Value Change Dump) or CSV timestamped transitions to digital state streams using Python (`vcdvcd` or regex transition finders).
* **Firmware & Non-Volatile Memory (NOR Flash):**
  - **Flash Memory Dumping & Modification (Winbond W25Qxx SPI NOR Flash):**
    - Commands: `0x03` (Read Data + 24-bit addr), `0x06` (Write Enable / WREN), `0x20` (Sector Erase 4KB + 24-bit addr), `0x02` (Page Program $\le$ 256 bytes + 24-bit addr), `0x05` (Read Status Register, poll WIP bit 0 $\to$ 0).
    - *Hardware Write Invariant:* NOR flash programming can only flip bits from $1 \to 0$. To overwrite non-$0\text{xFF}$ data (e.g. hash modification), you must: (1) read the full 4KB sector, (2) patch data in memory, (3) execute `WREN` + Sector Erase `0x20` to reset all bytes to `0xFF`, (4) execute `WREN` + Page Program `0x02` in 256-byte chunks.
  - **Firmware Inspection:** `binwalk -Me firmware.bin` (carve SquashFS, CramFS, JFFS2, UBI, raw Linux kernels).
  - **Microcontroller Architectures & CPU Hardware Bugs:**
    - **MOS 6502:** Reset vector at `$FFFC-$FFFD` loads startup PC.
    - *`JMP ($xxFF)` Bug:* In indirect jumps where address ends in `$FF`, the MSB is erroneously fetched from `$xx00` instead of `$(xx+1)00` due to 8-bit page counter non-carry. Bypass by staging vector into internal RAM and jumping indirect without crossing page boundaries.
    - **ARM / MIPS / RISC-V:** ARM (Thumb/ARM mode), MIPS (MIPS32/64, Big/Little endian - check opcode `0x03e00008` `jr $ra`), RISC-V (RV32I/RV64I, CH32V003), AVR (ATmega328P/Arduino).
  - **Emulation:** QEMU user space (`qemu-arm-static`, `qemu-mips-static`, `qemu-riscv32-static`).
* **Fault Injection & Side-Channel Analysis (SCA):**
  - **Power Analysis:** Simple Power Analysis (SPA) & Correlation Power Analysis (CPA) targeting AES S-Box substitutions ($H(k) = HW(SBOX(p \oplus k))$) or RSA modular exponentiation (square-and-multiply leakage).
  - **Clock & Voltage Glitching:** Crowbar circuits (MOSFET pulling $V_{CC}$ to ground for nanoseconds) targeting clock cycles during loop count comparisons (`BNE`/`BEQ`) or password checking routines to flip instruction branches or bypass signature checks.
  - Multitools: ChipWhisperer, CuriousBolt, Facedancer.
* **Wireless & RF Protocols:**
  - **Bluetooth Low Energy (BLE):** GATT profile, Services, Characteristics, Descriptors. Enumeration via `bleah`, `gatttool -b <MAC> -I`, `bluetoothctl`, or Python `bleak`. Attack vectors: unauthenticated read/write characteristics, replay of authorization handles.
  - **SDR / Sub-GHz RF:** RTL-SDR, HackRF, GNU Radio, URH (Universal Radio Hacker), Inspectrum. Modulations: AM/ASK, OOK (On-Off Keying for rolling codes/garage doors), FM/FSK, PSK.
  - **OOK / PWM Rolling-Code Analysis & Baseband Demodulation:**
    - *Demodulation:* Ingest interleaved complex float32 I/Q (`.cf32`), compute magnitude envelope $A = \sqrt{I^2 + Q^2}$, threshold into binary states.
    - *Symbol Extraction:* Identify pulse-width modulation (PWM) where symbol duration is constant (e.g., $1.0\text{ ms} = 1000\text{ samples}$) and high time indicates bit value (e.g., $300\ \mu\text{s} \to 0$, $600\ \mu\text{s} \to 1$).
    - *Frame Alignment:* Segment burst by inter-frame idle periods ($> 1.5\text{ ms}$). Look for $N$-bit payload + trailing stop pulse.
    - *Rolling Counter & Checksum Recovery:* Compare frames vertically. Static bits represent Remote ID / Serial (e.g., 32-bit `24ae4909`). Changing bytes reveal counter progression (e.g., $+7$ linear delta) and trailing checksums/CRCs (e.g. nibble sum modulo 15 or linear offset $\sum \text{nibbles} - 56$). Predict next frame without key recovery.

---

## 12. Cloud & AWS IAM Security
* **Lambda `iam:PassRole` Privilege Escalation:**
  - An entity with `lambda:CreateFunction`, `lambda:InvokeFunction`, and `iam:PassRole` on a service role (e.g. `ci-runner-role`) can deploy a Lambda function that executes under that role and exfiltrates its temporary STS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`).
* **Cross-Account Trust Exploitation (`sts:AssumeRole`):**
  - Roles with permissive trust relationships allow lateral movement across accounts without MFA or IP restrictions.
* **Confused Deputy Mitigation & `ExternalId` Secret Exfiltration:**
  - When third-party cross-account roles require an `sts:ExternalId` condition, extracting the configured `ExternalId` from misconfigured storage (e.g. partner S3 buckets or configuration files) allows unauthorized callers to assume the hardened role and access sensitive crown vaults.

---

## 13. Cryptography & Hardware Public Key Generation
* **Batch GCD / Shared Prime Factorization (Factorable Keys):**
  - Occurs when IoT/embedded devices or fleets manufactured on identical assembly lines use low-entropy PRNG seeds.
  - Distinct devices share a single prime factor ($N_1 = p \cdot q_1$, $N_2 = p \cdot q_2$).
  - Pairwise GCD computation $gcd(N_i, N_j)$ across public certificates rapidly extracts $p$.
  - Once $p$ is recovered, calculate $q = N/p$, $\phi(N) = (p - 1)(q - 1)$, and $d = e^{-1} \pmod{\phi(N)}$.
  - Decrypt RSA/PKCS#1 v1.5 ciphertexts by stripping prefix ``\x00\x02[padding]\x00[data]``.

---

## 14. Binary Exploitation & Linux ROP (glibc 2.34 - 2.39+)
* **Two-Stage ret2libc with Partial RELRO / No PIE:**
  - When binaries lack Stack Canaries and PIE (`ET_EXEC`), code addresses (`puts@plt`, `main`, gadgets) and `.got.plt` entries are statically located at fixed virtual addresses.
  - **Stage 1 (Information Leak):**
    - Payload: `[padding to RIP] + pop_rdi_ret + puts@got + puts@plt + main`
    - Prints raw bytes of resolved `puts@got` in libc, then loops execution cleanly back to `main()`.
    - Compute `libc_base = puts_leak - libc.symbols['puts']`.
  - **Stage 2 (Spawning Shell with 16-Byte Stack Alignment):**
    - x86-64 AII requires the stack pointer `RSP` to be 16-byte aligned before entering functions using SSE/AVX instructions (e.g. `system()` calling `do_system` / `movaps`).
    - Prepend a single `ret` gadget before `pop rdi`:
      `[padding to RIP] + ret + pop_rdi_ret + binsh_addr + system_addr`
    - Executes `system("/bin/sh")` cleanly without crashing on `movaps`.

---

## 15. Format String Arbitrary Writes (No PIE glibc 2)
**Null-Byte Pointer Alignment via Specifier-First Payloads:**
  - When ``printf(buf)` is called directly with user-controlled input, the format string parser can be leveraged for arbitrary read/``\%n`` writes.
  - In 64-bit binaries without PIE (`et_type = ET_EXEC`, base `0x400000`), target global variables in `.bss` (e.g. `0x40407c`) have fixed, static addresses.
  - **Two-Byte / Null-Byte Caveat:** Addresses in middle-range address spaces contain high-order null bytes (`0x000000000040407c`). Placing the pointer at the start of `user_bub` would cause `printf` to terminate at the first null byte before executing specifiers.
  - **Solution (Specifier-First Alignment):**
    - Calculate the format argument index of the start of `user_bub` (usually argument 6 on x86-64 System V ABI).
    - Place the format specifiers (e.g. `%n / %lhn / %hhn` with desired character count widths like `%1337c%n``)`at the front of the buffer.
    - Pad the specifiers with non-null bytes (e.g. `A`) to an 8-byte boundary that lands
      exactly at an offset slot $K=6 + \latflen(\text{specifiers}) / 8$.
    - Append the 64-bit target pointer (`p64(addr)`) immediately after the padding.
    - The specifier `%K-n` references the 64-bit pointer perfectly without hindring format parsing.

---

## 16. Seccomp Sandbox Filtering & ORW Shellcode
* **Seccomp Default Kill with IOOnly Whitelisting:**
  - When ``seccomp_init(SCMP_ACT_KILL)` is used, any non-whitelisted syscall instantly terminates the thread/process (`SIGSYS`).
  - Challenges blocking `execve` (59) and `execveat` (322) often permit ``open` (2), `openat` (257), `read` (0), `write` (1), and `exit` (60).
  - **Open-Read-Write (ORW) Shellcode Pattern (x86-64):**
    1. Stage target filename on stack (e.g. `/flag\0`, `flag.txt\0`).
    2. `sys_open(rsp, O_RDONLY=0)`:
       ``bx 02 00 00 00 0o 05`` returns file descriptor in `movsx ray, eax`.
    3. `sys_read(fd, rsp, 128)`:
       `syscall` into stack buffer.
    4. `sys_write(1, rsp, count)`:
       `mov edx, eax; mov edi, 1; mov rsi, rsp; mov eax, 1; syscall`` to dump contents directly to stdout.
    5. ``sys_exit(0)`:
       `mov eax, 60; syscall`, preventing crashes or unwanted subsequent instruction execution.

---

## 17. x86-64 ret2win Stack Alignment Dynamics
* **16-Byte ABI Accounting for Win Functions:**
  - x86-64 System V ABI requires RSP % 16 == 0 immediately before any call instruction (and RSP % 16 == 8 at function entry).
  - When overwriting a return address directly with win():
    1. If the vulnerable function executes leave; ret into win():
       - Executing win directly without an intermediate 
et gadget often already satisfies the 16-byte alignment when win performs push rbp followed by sub rsp, multiple_of_16.
    2. Trial Vectors:
       - Vector A: p64(win)
       - Vector B: p64(ret) + p64(win) (adds 8 bytes to RSP)
       - Vector C: p64(win + 5) (skips push rbp; mov rbp, rsp)

---

## 18. AFSK Audio Covert Channel & Bell 202 / 300-Baud Demodulation
* **Detection & Pipeline:**
  1. **RMS Energy Profiling:**
     - Compute windowed RMS energy across audio tracks (e.g. 100ms chunks) to isolate discrete signal bursts embedded within ambient room noise.
  2. **Frequency Identification:**
     - Take FFT of the active window. Peak clusters around 1200 Hz (Mark) and 2200 Hz (Space) signify Bell 202 standard AFSK tones.
     - Observe the initial carrier burst (typically 100–200ms of unmodulated 1200 Hz) to calibrate the preamble.
  3. **Discriminator Implementation:**
     - Apply bandpass filtering around the carrier region (1000–2400 Hz).
     - Calculate instantaneous frequency via analytic signal phase derivative:
       inst_freq = np.diff(np.unwrap(np.angle(hilbert(filtered)))) * sr / (2 * np.pi)
     - Smooth with a low-pass filter configured to the expected symbol rate (e.g. 600 Hz cutoff).
     - Center deviation around (f_mark + f_space) / 2 = 1700 Hz.
  4. **Baud Rate Calibration & Framing:**
     - Measure symbol transitions; consecutive run-lengths indicate the baud rate.
     - If run-lengths cluster at multiples of 4 samples relative to 1200 baud, the transmission is 300 baud (samples_per_bit = sample_rate / 300).
     - Demodulate via standard asynchronous serial UART (8N1: start bit = 0, 8 data bits LSB first, stop bit = 1).

---

## 19. Android Component Security: ContentProvider Traversal & WebView Deep Link Prefix Bypass
* **Exported ContentProvider Path Traversal:**
  - **Mechanic:** ContentProvider.openFile(Uri uri, String mode) implementations that strip a static path prefix (e.g. /files/) and append the rest directly to a base directory (
ew File(baseDir, path)) without canonicalization.
  - **Verification:** An attacker queries content://<authority>/files/../../<target> using db shell content read --uri ....
  - **Defense/Remediation:** Enforce canonical path containment:
    if (!file.getCanonicalPath().startsWith(baseDir.getCanonicalPath())) throw new SecurityException();
* **WebView Deep Link Origin Validation Flaws:**
  - **Mechanic:** Deep-link handlers (RouterActivity) forwarding external ?url= parameters to internal WebViewActivity instances.
  - **Validation Flaw:** Verifying destinations with url.startsWith(baseUrl).
  - **Impact:** http://expected-domain@attacker-domain/ satisfies startsWith("http://expected-domain") but routes to ttacker-domain, leaking headers passed via loadUrl(url, headers).
  - **Defense/Remediation:** Parse the URI into ndroid.net.Uri and strictly validate uri.getHost(), uri.getScheme(), and uri.getPort() against an allowlist.

---

## 20. SDR & RF: 2-FSK Demodulation and CC1101 Packet Recovery
* **Raw Baseband Complex I/Q (cf32):**
  - **Structure:** Interleaved 32-bit floats [I0, Q0, I1, Q1, ...]. Load via np.fromfile(path, dtype=np.complex64).
  - **Burst Boundary Isolation:** Scan absolute magnitude |z| = sqrt(I^2 + Q^2). Locate the steep envelope rise and fall to isolate active transmission bursts.
  - **Spectral Peak Identification:** Compute FFT spectrum np.fft.fft(signal) to determine the Mark (f1) and Space (f0) tone frequencies and center carrier fc = (f0 + f1) / 2, delta_f = (f1 - f0) / 2.
  - **Baud Rate Estimation:** Spectral sidebands or autocorrelation / run-length analysis of instantaneous frequency transitions reveal the symbol period and baud rate Rs = fs / samples_per_symbol.
* **Demodulation via Tone Correlation:**
  - For each symbol window of length N, correlate with reference complex sinusoids exp(2j * pi * f1 * t) and exp(2j * pi * f0 * t).
  - Bit decision: c(f1) > c(f0) -> 1, else 0.
* **CC1101 Transceiver Packet Architecture:**
  - **Preamble:** Alternating 10101010 (0xAA) bytes (typically 4-8 bytes) for receiver AGC and bit synchronization.
  - **Sync Word:** Standard 2-byte sync words (e.g. 0x2D 0xD4 or 0xD3 0x91).
  - **Framing:**
    - Byte 0: Packet length L (number of payload bytes).
    - Bytes 1..L: Payload data (ASCII text, flags, sensor data).
    - Trailing 2 bytes: CRC-16-CCITT (polynomial 0x1021, init 0xFFFF) calculated over [length + payload].

---

## 21. Hardware Side-Channel Analysis: Correlation Power Analysis (CPA) on AES-128
* **Target Operation & Intermediate State:**
  - In AES-128 encryption, Round 1 XORs plaintext $P$ with Round Key $K_0$, followed by SubBytes non-linear substitution:
    $$Y_{n, i} = \text{SBox}(P_{n, i} \oplus K_i) \quad \text{for byte } i \in [0, 15], \text{ trace } n \in [0, N-1]$$
* **Power Leakage Model:**
  - Dynamic power dissipation in CMOS logic is dominated by bit switching (Hamming Distance) and bus/register charge states (Hamming Weight):
    $$H_{k, n} = \text{HW}(\text{SBox}(P_{n, i} \oplus k)) \quad \text{for candidate } k \in [0, 255]$$
* **Vectorized Pearson Correlation Coefficient:**
  - Center the $N \times T$ trace matrix $T$ and $256 \times N$ hypothesis matrix $H$:
    $$\tilde{T} = T - \bar{T}, \quad \sigma_T = \sqrt{\sum \tilde{T}^2}$$
    $$\tilde{H} = H - \bar{H}, \quad \sigma_H = \sqrt{\sum \tilde{H}^2}$$
  - Compute the correlation matrix via single matrix multiplication:
    $$\rho = \frac{\tilde{H} \cdot \tilde{T}}{\sigma_H \cdot \sigma_T} \quad (256 \times T)$$
  - For each byte $i$, select $\hat{k} = \arg\max_{k} \max_{t} |\rho_{k, t}|$.
* **Diagnostic Indicators:**
  - **Peak Magnitude:** Strong correlation peak ($|\rho| \ge 0.60$) decisively separates the true key byte from incorrect hypotheses ($|\rho| \le 0.20$).
  - **Temporal Stride:** In microcontroller/smart-card software AES implementations, the S-box operations execute sequentially in a loop, resulting in equidistant sample peaks (e.g. $t_i = t_0 + i \cdot \Delta t$).

---

## 22. WebAuthn / FIDO2 Attestation Bypass: ASN.1 Tag Confusion & Relative Offset Bugs
* **Vulnerability Class:** ASN.1 Context-Tag Confusion in Custom X.509 Certificate Extensions.
* **Mechanism & Pitfall:**
  - WebAuthn Relying Parties supporting enterprise / air-gapped authenticators often inspect custom certificate extensions (e.g. `AuthenticatorPolicy` carrying security tiers or `elevated` privileges).
  - When parsers migrate from positional decoding to dynamic tag calculation relative to variable sections (like `aaguids SEQUENCE OF OCTET STRING`), bugs in tag offset calculations cause the parser to consult an adjacent context tag (e.g. Tag 8 instead of Tag 7) for authorization flags.
  - Standard policy validators may reject direct assertion of elevated privileges on the canonical tag (`tag 7 = True` $\to$ `403 attestation rejected`).
* **Exploitation Pattern:**
  - Craft a self-signed X.509 attestation certificate with an AAGUID not listed in MDS3 (routing to legacy/self-enrolled parsing).
  - In the custom extension DER encoding, supply the canonical tag as `False` (`0x87 01 00`) to pass validation sanity checks, while supplying the calculated relative tag as `True` (`0x88 01 01`).
  - Both tags are preserved in ascending order in the DER SEQUENCE. The parser validates the canonical field, but reads the authorization state from the shifted tag, successfully enrolling at the elevated / enterprise tier.

---

## 23. Solana Web3: Liquidation Denial of Service via Compute Budget Exhaustion
* **Vulnerability Class:** Unbounded Loop Execution in Solana Smart Contracts.
* **Mechanism & Pitfall:**
  - In Solana lending protocols, liquidation logic typically verifies position health by summing collateral value and debt across all open positions in an obligation account.
  - Transactions on Solana operate under a strict Compute Unit (CU) budget (default 200,000 CU, maximum 1,400,000 CU).
  - If a protocol allows users to batch-open positions (`Ix::OpenMany`) where zero collateral and zero debt satisfy the health constraint ($0 \le 0 \cdot \text{LTV}$), an attacker borrower anticipating liquidation can pad the obligation with thousands of zero-cost positions.
* **Exploitation Pattern:**
  - Identify batch position opening functions without strict upper bounds on individual transactions.
  - Submit `OpenMany` with `count = 10000` (collateral=0, debt=0).
  - When the market price drops and the borrower becomes underwater, keeper bots attempting to trigger `Ix::Liquidate` exhaust their compute budget inside the loop over positions ($O(N)$ SBF operations), causing the liquidation transaction to revert.
  - The collateral cannot be seized, resulting in permanent default without clawback.

---

## 24. Custom VM Reversing & SPN Cipher Inversion for Cryptographic Key Custody
* **Vulnerability Class / Reversing Pattern:** Distributed Custom Virtual Machine Agent Bytecode with Cryptographic Obfuscation.
* **Mechanism & Pitfall:**
  - Proprietary key-custody / shard systems distribute root custody seeds across multiple autonomous agent executables/shards.
  - Shards encapsulate custom VM bytecode executing over virtual registers (e.g. 14 registers $r_0 \dots r_{13}$, 32-bit width).
  - VM instructions alternate between non-linear S-box substitutions and linear permutations (Substitution-Permutation Network, SPN).
  - When agents employ bit-masking operations (e.g. `AND_IMM` clearing bits of intermediate registers before S-box lookups), forward VM execution loses information, resulting in $2^k$ candidate inputs that all satisfy the terminal assertion constraints (`CMP` / `ASSERT_EQ`).
* **Analytical Inversion Pipeline:**
  1. **Jump Table & Opcode Recovery:** Disassemble the runtime VM dispatch loop to extract instruction boundaries, argument sizing, and register mapping.
  2. **Template Matching Across Shards:** Even when decode tables are scrambled or encrypted across shards, bytecode structure remains invariant (identical opcode boundaries and register operands). Reconstruct decode tables by mapping template opcode positions directly to the raw opcode bytes.
  3. **Analytical Cipher Inversion:** Rather than relying on heavyweight SMT constraint solvers (which experience combinatorial explosion with nested 256-case S-box ASTs), run the SPN cipher backwards from final assertion constants:
     - Invert linear register XOR mixing by executing XOR assignments in reverse order ($r_a \oplus= r_b$ is self-inverse).
     - Invert S-box substitutions using the precomputed permutation inverse $\text{SBOX}^{-1}$.
     - Branch across masked bit combinations to enumerate the exact $2^k$ input key candidates in milliseconds.
  4. **Public Key Disambiguation:** Concat candidate fragments in valid chain permutations and test against the instance's public key (e.g. Ed25519 scalar multiplication $A = a \cdot B$). An exact 256-bit public key match uniquely resolves the true seed and eliminates all ambiguous masking bits.
   5. **Instance Handout Synchronization:** In distributed cloud CTFs where challenge instances initialize a fresh keypair on container start, verify if the live service serves its synchronized shard archive (e.g. /handout.tar.gz) directly over HTTP before attempting attestation with stale handout keys.

---

## 25. Attestation Core Graph Traversal & Decoupled ARX Inversion
* **Challenge Paradigm:** Dynamic VM State Graph with Cryptographic Signature Verification (`countersign`).
* **Mechanism & Pitfall:**
  - The runtime executes a DAG of bytecode basic blocks connected by signed edges. Each edge transition requires a valid MAC tag (e.g. 6-byte SipHash-2-4 over `src || dst || cond || salt`).
  - The graph image returned by diagnostic commands (`GET`) contains dummy/decoy edges alongside authentic edges. An attestation oracle (`MINT`) computes MAC tags on arbitrary input buffers <= 16 bytes.
  - Querying `MINT` across all edge descriptors deterministically eliminates decoy edges, reducing a deceptive graph into a clean, 12-round diamond ladder.
* **Analytical Inversion Pipeline:**
  1. **Decoupled State Channels:** Observe register dependencies across the round functions. In the 12 rounds, the primary ARX permutation operates solely on (r0, r1, r2, r3) without reading (r4, r5), while intermediate branching nodes only modify (r4, r5).
  2. **Backward Permutation Step:** Because (r0..r3) never branches or depends on other registers, the 12 ARX rounds are strictly bijective. Invert the ARX operations backward from the final target assertions (T0..T3) to recover initial (r0..r3) in O(1) operations:
     r2 = r2 ^ imm2; r0 = r0 - imm1; r1 = r1 ^ r3; r3 = (r3 >>> rot2) - r2; r2 = r2 ^ r0; r0 = (r0 >>> rot1) - r1
  3. **Exact Path Reconstruction:** Simulate (r0..r3) forward from initial state to evaluate all 12 branch bits deterministically.
  4. **Secondary Channel Inversion:** Trace the selected intermediate nodes backward to invert (r4, r5) from (T4, T5) using the inverse operations:
     r5 = (r5 >>> rot_r5) - r4; r4 = r4 ^ imm_xor
  5. Concatenate the recovered 32-bit words into the 24-byte input to steer execution directly to the flag emission block.

---

## 26. Bare-Metal x86 BIOS ROM Reversing & Multi-Plane Matrix Reconstruction
* **Challenge Paradigm:** Raw x86 MBR / Real-Mode BIOS Display Controller (`afterglow`).
* **Mechanism & Pitfall:**
  - Firmware boots directly from MBR (`0x7C00`), reads payload into `0x8000` via `INT 13h, AH=02h`, sets VGA Mode `13h` (320x200 256 colors), and displays a dummy factory calibration pattern while idling for service code input.
  - Entering the correct 32-bit service code triggers decryption of 8 bitplanes that composite a 256x32 matrix display.
* **Analytical Reconstruction Pipeline:**
  1. **Seed & Service Code Extraction:** Identify the ROM offset (e.g. `0x83d6` in payload) holding the 32-bit PRNG seed. Trace arithmetic transformations (XOR mixing, Murmur-style multiplicative constants `0x9e3779b1`, `0x85ebca77`) to derive the service code and initial LFSR state.
  2. **LFSR State Machine:** Accurately replicate 16-bit Galois/Fibonacci LFSR step logic (b15 ^ b13 ^ b12 ^ b10) to regenerate the plane permutation (`perm[0..7]`), bit inversion flags, and (dx, dy) coordinate shifts.
     - *Critical Pitfall:* Maintain exact function call order (e.g. interleaved dx then dy calls in loop body vs separate array passes) to ensure PRNG alignment.
  3. **LCG Keystream Decryption:** Emulate the per-plane Linear Congruential Generator (state = state * 0x19660d + 0x3c6ef35f) seeded with ((bp + 1) * 0x1000193) ^ service_code to decrypt the raw 1024-byte plane buffers.
  4. **Spatial Matrix Reassembly:** Map each pixel (x, y) through cyclic shift offsets: xs = (x + dx) % 256, ys = (y + dy) % 32. Accumulate bits into the final 8-bit grayscale frame buffer: pixel |= (bit << perm[bp]).
  5. **Visual Recovery:** Export the decoded buffer directly to an 8-bit grayscale image (`.png` / `.pbm`) to render the service tag flag text with 100% optical clarity.
---

## 27. Exposed Git Object Carving & Session JWT Forgery for Role Escalation
* **Challenge Paradigm:** Production web deployment with exposed source repository (`worldoutter`).
* **Mechanism & Pitfall:**
  - Web servers inadvertently serving the root directory often expose `/.git/`. Even when directory listing is disabled (HTTP 403 / 404 on `/.git/`), raw Git objects (`/.git/objects/xx/yy...`), HEAD (`/.git/HEAD`), and refs (`/.git/refs/heads/<branch>`) remain directly downloadable.
  - Session management using signed JSON Web Tokens (e.g. HS256) relies entirely on the confidentiality of the signing secret (`JWT_SECRET`).
* **Extraction & Exploitation Pipeline:**
  1. **Git Object Traversal:**
     - Query `/.git/HEAD` to resolve the active branch (e.g. `ref: refs/heads/main`).
     - Query `/.git/refs/heads/main` to retrieve the latest commit SHA.
     - Fetch `/.git/objects/<sha[:2]>/<sha[2:]>`, decompress with zlib, and extract the tree SHA.
     - Recursively parse the Git tree entries `[mode] [name]\0[20-byte-sha]` to locate configuration files (e.g. `config/secret.js`) and server routing logic (`server.js`).
  2. **Secret Extraction & Session Forgery:**
     - Extract `JWT_SECRET` directly from uncompressed blob objects.
     - Inspect `server.js` role validation logic (`req.claims.role === 'commissioner'`).
     - Construct a forged JWT payload with elevated privilege (`{"user":"you","team":"...","role":"commissioner"}`) and sign with HMAC-SHA256 using the recovered secret.
  3. **Privileged Access:**
     - Set the forged token in the session cookie (e.g. `wo_session`) and request the privileged console (`/commissioner`) to extract the flag.

