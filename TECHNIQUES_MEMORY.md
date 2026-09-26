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

---

## 9. Binary Exploitation & Reverse Engineering Tooling
* **Installed Python Frameworks:**
  - `pwntools`: Standard ELF, ROP, process/remote I/O, cyclic patterns, format-string solver.
  - `ptrlib`: Lightweight CTF library by ptr-yudai for fast binary/crypto interactions (`from ptrlib import *`).
* **IDA Pro Live MCP Server (`tools/pcm`):**
  - If IDA Pro is running locally, `tools/pcm` acts as a Model Context Protocol server connecting directly to Hex-Rays decompiler, basic block graphs, cross-references, and IDAPython REPL.

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

