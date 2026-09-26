---
challenge: boardroom_av
category: web
techniques: [hls_stream_discovery, audio_burst_analysis, afsk_demodulation, bell_202_300baud_uart]
time_to_flag: 45
status: solved
---

# Boardroom AV - Solution Writeup

## Challenge Overview
- **Target URL:** `https://web-17e4256823c5a05c.web.h7tex.com`
- **Description:** The boardroom's always-on AV bridge got quietly compromised, streaming its live feed while walking secrets out the door without alerting listeners.
- **Flag:** `H7CTF{2fb1aabd-652b-4ff7-b700-2af47886108e}`

## Vulnerability & Exfiltration Vector
1. **Directory Discovery:**
   - Top-level path fuzzing on port 443 with trailing slash redirect inspection revealed `/boardroom` (301 Moved Permanently to `/boardroom/`).
   - Requesting `/boardroom/index.m3u8` delivered an HLS VOD playlist containing 6 MPEG-TS audio segments (`seg_000.ts` through `seg_005.ts`).

2. **Audio Stream Extraction:**
   - Concatenating the TS segments and decoding the AAC stream via PyAV yielded ~5.70 seconds of mono audio sampled at 48,000 Hz.
   - Background audio remained low-amplitude ambient noise (~700–900 RMS).
   - An intentional data burst occurred between 2.021s and 3.695s (sample range 97,025 to 177,343), jumping to ~11,500 RMS.

3. **Modulation Analysis & Demodulation:**
   - Spectral analysis of the burst revealed dual-tone AFSK (Audio Frequency Shift Keying) with:
     - Mark frequency: `1200 Hz`
     - Space frequency: `2200 Hz`
   - Initial 160ms preamble consisted of a pure 1200 Hz carrier.
   - Demodulating with an instantaneous frequency discriminator (Hilbert transform) followed by a low-pass filter at 600 Hz established the symbol rate as **300 baud** (160 samples per bit at 48 kHz).
   - Standard UART framing (8N1: start bit = 0, 8 data bits LSB first, stop bit = 1) recovered the plaintext ASCII payload containing the flag.

## Solver
The automated Python solver is located at `solutions/boardroom_av/solve.py`.
It downloads the playlist, fetches segments, extracts the audio burst, discriminates the frequencies, decodes 300 baud UART, and prints the verified flag.
