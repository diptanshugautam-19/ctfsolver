---
challenge: afterglow
category: rev
techniques: [bios-reversing, lfsr, lcg-decryption, matrix-rendering]
time_to_flag: 12
status: solved
---

# Afterglow — Solution Notes

## Overview
Afterglow provides a raw 32KB disk image (`panel.rom`) dumped from an airport departure board controller flash.
The image boots in a standard x86 PC environment (`qemu-system-i386 -drive format=raw,file=panel.rom`).
In normal standby mode, the board runs self-tests and flickers, showing a static factory calibration test string. Entering the correct 32-bit service code on the keypad triggers the firmware to decrypt and render the board's true unique service tag across the matrix display.

## Technical Details & Architecture

### 1. Bootloader & Payload Structure
- **Sector 0 (0x000..0x1FF)**: MBR bootloader at address `0x7C00`. Uses BIOS `INT 13h, AH=02h` to read 63 sectors (32,256 bytes) starting from sector 2 into memory address `0x8000`, then far-jumps (`ljmp 0:0x8000`).
- **Main Firmware (0x8000)**:
  - Sets VGA video mode `13h` (320x200 256 colors) via `INT 10h, AX=0013h`.
  - Configures VGA palette DAC (ports `0x3c8` / `0x3c9`) to a 256-level grayscale ramp ($RGB = (c \gg 2, c \gg 2, c \gg 2)$).
  - Initializes seeds and key material at function `0x8049`.
  - Enters standby loop at `0x8026`: cycling standby frames at `0x8186` and reading keypad input via `INT 16h` at `0x81fa`.

### 2. Service Code Derivation
The firmware reads a 32-bit seed at offset `0x83d6` (in payload):
```python
eax = seed
eax = (eax ^ 0x5bd1e995) & 0xffffffff
eax = (eax * 0x9e3779b1) & 0xffffffff
eax ^= (eax >> 15)
eax = (eax * 0x85ebca77) & 0xffffffff
eax ^= (eax >> 13)
service_code = eax
```
When keypad input hex digits followed by Enter (`0x0D`) match `service_code`, the firmware calls the decryption routine `0x825f` followed by display routine `0x8364`.

### 3. Display Decryption & De-obfuscation
The target display is a 256x32 matrix (8,192 pixels).
The image is split across 8 encrypted planes (1,024 bytes each) located at `0x83dc + bp * 1024`:
1. **LFSR Parameter Derivation**:
   - Initial LFSR state: `(service_code ^ (service_code >> 16)) & 0xffff` (or `0xbeef` if 0).
   - Polynomial feedback: $b_{15} \oplus b_{13} \oplus b_{12} \oplus b_{10}$.
   - Derives:
     - Plane bit permutation `perm[0..7]` via Fisher-Yates shuffle.
     - Plane polarity invert mask `invert[0..7]` (1 bit each).
     - Signed coordinate shifts `dx[0..7]` and `dy[0..7]` in range $[-2, 2]$.
2. **LCG Keystream Decryption**:
   - For plane `bp` ($0 \dots 7$):
     - Initial state: $(((bp + 1) \times \text{0x1000193}) \oplus \text{service\_code}) \pmod{2^{32}}$.
     - LCG recurrence: $\text{state} \leftarrow \text{state} \times \text{0x19660d} + \text{0x3c6ef35f} \pmod{2^{32}}$.
     - Keystream byte: $\text{state} \gg 24$.
     - Decrypts 1,024 bytes: $\text{dec}[i] = \text{enc}[i] \oplus \text{keystream}$.
3. **Spatial Reconstruction**:
   - For each pixel $(x, y) \in [0, 255] \times [0, 31]$:
     - Source coordinates: $x_s = (x + dx) \pmod{256}$, $y_s = (y + dy) \pmod{32}$.
     - Bit index: $\text{bit} = (\text{dec}[(y_s \times 256 + x_s) / 8] \gg (7 - (x_s \bmod 8))) \oplus \text{inv}$.
     - If bit is 1: $\text{image}[y, x] \mathrel{|}= (1 \ll \text{perm}[bp])$.

### 4. Tag Recovery
Rendering the resulting 256x32 matrix reveals the crisp unit service tag:
`H7CTF{ad9e53f3-904e-4662-b201-c97dfc094a24}`

## Flag
`H7CTF{ad9e53f3-904e-4662-b201-c97dfc094a24}`
