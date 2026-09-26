---
challenge: garage_remote
category: hardware
techniques: [rf_ook, pwm_demodulation, rolling_code, checksum_prediction]
time_to_flag: 15
status: solved
---

# Garage Remote — Writeup

## 1. Challenge Overview
- **Instance URL:** `https://web-ae0648197b3162a2.web.h7tex.com`
- **Artifact:** `capture.cf32` (interleaved float32 complex baseband I/Q, $f_s = 1,000,000 \text{ Hz}$).
- **Target Endpoint:** `POST /unlock` accepting `{"code": "<12 hex digits = 48 bits>"}`.
- **Description:** 8 captured transmissions of a cheap rolling-code garage remote (433 MHz, On-Off Keying).

## 2. Signal Analysis & Demodulation
1. **Sampling & Modulation:**
   - Sample rate: $1 \text{ MS/s}$.
   - Complex baseband magnitude: envelope threshold at $0.5$.
   - Modulation: On-Off Keying (OOK) with Pulse Width Modulation (PWM).
   - Symbol duration: $1.0 \text{ ms}$ ($1000$ samples).
   - Bit 0: High for $300 \ \mu\text{s}$, Low for $700 \ \mu\text{s}$.
   - Bit 1: High for $600 \ \mu\text{s}$, Low for $400 \ \mu\text{s}$.
   - Frame boundary: Inter-frame silence $> 3.0 \text{ ms}$ ($3100$ samples).
2. **Frames Extracted (48 bits each + trailing pulse):**
   - Frame 0: `24ae49095081`
   - Frame 1: `24ae49095788`
   - Frame 2: `24ae49095e8f`
   - Frame 3: `24ae49096587`
   - Frame 4: `24ae49096c8e`
   - Frame 5: `24ae49097386`
   - Frame 6: `24ae49097a8d`
   - Frame 7: `24ae49098185`

## 3. Rolling Code Modeling & Prediction
1. **Fixed Serial / ID:**
   - The first 4 bytes (32 bits) are static across all frames: `24ae4909`.
2. **Rolling Counter (Byte 4):**
   - `0x50` (80) $\to$ `0x57` (87) $\to$ `0x5e` (94) $\to \dots \to$ `0x81` (129).
   - Progression: Linear increment of $+7$ per button press.
   - For frame 8: $129 + 7 = 136 = \text{0x88}$.
3. **Checksum (Byte 5):**
   - High nibble is static: `0x8`.
   - Low nibble satisfies:
     $$\text{last\_nibble} = \sum_{i=1}^{10} \text{nibble}_i - 56 = (7k \pmod{15}) + 1$$
   - For frame 8 ($k=8$):
     $$\text{sum}(\text{nibbles}_{0..9}) = 52 + 16 = 68 \implies 68 - 56 = 12 = \text{0xc}$$
   - Byte 5 is therefore `0x8c`.
4. **Predicted Frame 8:**
   `24ae4909888c`

## 4. Verification & Flag Recovery
- Submitting `{"code": "24ae4909888c"}` to `POST /unlock` unlocks the receiver:
```json
{"status": "unlocked", "flag": "H7CTF{e2b056ce-ecca-4aa9-be36-186aceaf039f}"}
```
- Flag: `H7CTF{e2b056ce-ecca-4aa9-be36-186aceaf039f}`
