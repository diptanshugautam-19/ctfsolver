---
challenge: field_capture
category: hardware
techniques: [sdr_rf, fsk_demodulation, cc1101_framing, crc16_ccitt]
time_to_flag: 10
status: solved
---

# Field Capture (Unknown Transmission) — Writeup

## 1. Challenge Overview
- **Instance URL:** `https://web-372d030d5bcef7b1.web.h7tex.com`
- **Artifact:** `capture.cf32` (interleaved float32 complex baseband I/Q, $f_s = 1,000,000 \text{ Hz}$).
- **Description:** A single burst over the air near an unidentified device. No datasheet or protocol notes. Recover the message.

## 2. Signal Analysis & Demodulation
1. **Sampling & Spectrum Analysis:**
   - Sample rate: $f_s = 1 \text{ MS/s}$.
   - File length: $391,752$ bytes $\to 48,969$ complex samples ($\sim 49 \text{ ms}$).
   - Active burst range: sample index $2827$ to $46027$ (exactly $43,200$ samples).
   - FFT spectrum reveals two distinct tone peaks:
     - Mark frequency: $f_1 = 85 \text{ kHz}$
     - Space frequency: $f_0 = 35 \text{ kHz}$
     - Center frequency: $f_c = 60 \text{ kHz}$, deviation $\Delta f = \pm 25 \text{ kHz}$.
   - Sidebands spaced at $5 \text{ kHz} \implies$ Symbol rate $R_s = 10,000 \text{ baud}$ ($100$ samples per symbol).
   - Burst span: $43,200 / 100 = 432 \text{ symbols} = 54 \text{ bytes}$.

2. **FSK Demodulation:**
   - For each 100-sample block, compute correlation against baseband complex sinusoids $e^{j 2\pi f t}$ for $35 \text{ kHz}$ and $85 \text{ kHz}$.
   - Binary decision: $c(85\text{k}) > c(35\text{k}) \implies 1$, else $0$.
   - Phase difference ($\Delta \phi$) yields identical bitstream.

## 3. Packet Structure & Protocol Identification
- **Raw Hex Stream (54 bytes):**
  `aaaaaaaaaaaa2dd42b48374354467b65663236396663622d363766322d346666322d396665322d3435636338643563373063617d9e5e`
- **Framing (CC1101 standard RF transceiver packet format):**
  1. **Preamble:** `0xAA 0xAA 0xAA 0xAA 0xAA 0xAA` (6 bytes of alternating `10101010`).
  2. **Sync Word:** `0x2D 0xD4` (16-bit sync word default on CC1101 / Silicon Labs).
  3. **Length Byte:** `0x2B` ($43$ bytes).
  4. **Payload (43 bytes):**
     `H7CTF{ef269fcb-67f2-4ff2-9fe2-45cc8d5c70ca}`
  5. **CRC Checksum:** `0x9E 0x5E`.
     - Verified with standard CRC-16-CCITT ($\text{poly} = \text{0x1021}$, $\text{init} = \text{0xFFFF}$) over `[length + payload]`:
       $$\text{CRC16}(0\text{x2b} \mathbin{\Vert} \text{payload}) = 0\text{x9E5E} \quad (\text{Exact Match})$$

## 4. Recovered Flag
`H7CTF{ef269fcb-67f2-4ff2-9fe2-45cc8d5c70ca}`
