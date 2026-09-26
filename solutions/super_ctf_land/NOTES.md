---
challenge: super_ctf_land
category: forensics
techniques: [ROM-Analysis, GameBoy-Emulation, Headless-Simulation, HUD-Inspection, PyBoy]
time_to_flag: 4
status: solved
---

# Super CTF Land — Solution Notes

## Challenge Summary
- **Target File:** `Super CTF Land.gb` (Game Boy ROM, 64 KB, MBC1)
- **Category:** Forensics / Reverse Engineering
- **Objective:** Locate the secret left behind in the hacked ROM.

## Triage & Analysis
1. **File Identification & Header:**
   - Standard 65,536-byte Game Boy cartridge ROM.
   - Header title: `SUPER PIKA LAND` (a classic Game Boy romhack of *Super Mario Land*).
   - Checksums: Header `0xd0`, Global `0x5e35`.
2. **Flag Hunt / Strings Scan:**
   - Static string searches in the raw binary did not reveal readable flag text directly due to custom tile index / HUD tilemap encoding.
3. **Dynamic Emulation & Level Triage:**
   - Booted the ROM using a headless Python Game Boy emulator (`PyBoy`).
   - Simulating past the title screen and pressing `START` into World 1-1 loads the modified HUD tiles at the top of the display.
   - The HUD header (`BYUC  TF{   H@XER  TYM}`) replaces the standard status bar:
     - `BYUC TF{`
     - `H@XER`
     - `TYM}`

## Captured Evidence
- Frame buffer capture saved to [`solutions/super_ctf_land/screen.png`](file:///c:/Users/USER/OneDrive/Desktop/ctf/solutions/super_ctf_land/screen.png).

## Flags Recovered
- Expected format: `ctf{h@xertym}`
- Native event format: `byuctf{h@xertym}`
