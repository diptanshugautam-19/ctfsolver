#!/usr/bin/env python3
"""
Field Capture / Unknown Transmission Solver
Demodulates 2-FSK raw complex baseband I/Q (capture.cf32), parses CC1101 packet format,
verifies CRC-16 CCITT, and extracts flag.
"""

import os
import sys
import urllib.request
import numpy as np

CHALLENGE_URL = "https://web-372d030d5bcef7b1.web.h7tex.com"
CAPTURE_FILE = os.path.join(os.path.dirname(__file__), "capture.cf32")

def ensure_capture():
    if not os.path.exists(CAPTURE_FILE):
        print(f"[+] Downloading capture.cf32 from {CHALLENGE_URL}...")
        urllib.request.urlretrieve(f"{CHALLENGE_URL}/capture.cf32", CAPTURE_FILE)

def crc16_ccitt(data: bytes, init: int = 0xFFFF, poly: int = 0x1021) -> int:
    crc = init
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def solve():
    ensure_capture()
    data = np.fromfile(CAPTURE_FILE, dtype=np.complex64)
    mag = np.abs(data)

    # Locate burst start (energy threshold)
    threshold = 0.5
    active = np.where(mag > threshold)[0]
    if len(active) == 0:
        raise ValueError("No signal burst detected!")
    
    start_idx = active[0]
    # Refine exact burst start: find first sample where magnitude jumps above threshold
    for i in range(max(0, start_idx - 10), start_idx + 10):
        if mag[i] > threshold:
            start_idx = i
            break

    # Demodulate 2-FSK: 10 kbaud (100 samples/symbol at 1 MSps)
    # Mark: 85 kHz, Space: 35 kHz
    samples_per_symbol = 100
    t = np.arange(samples_per_symbol) / 1e6
    tone_35k = np.exp(2j * np.pi * 35000 * t)
    tone_85k = np.exp(2j * np.pi * 85000 * t)

    # Total burst symbols
    num_symbols = 432
    burst = data[start_idx : start_idx + num_symbols * samples_per_symbol]

    bits = []
    for i in range(num_symbols):
        block = burst[i * samples_per_symbol : (i + 1) * samples_per_symbol]
        c35 = np.abs(np.dot(block, np.conj(tone_35k)))
        c85 = np.abs(np.dot(block, np.conj(tone_85k)))
        bits.append(1 if c85 > c35 else 0)

    bitstr = "".join(map(str, bits))
    raw_bytes = bytearray()
    for i in range(0, len(bits), 8):
        raw_bytes.append(int(bitstr[i : i + 8], 2))

    raw_bytes = bytes(raw_bytes)

    # Look for sync word 0x2D 0xD4 (CC1101 default)
    sync_word = b"\x2d\xd4"
    sync_pos = raw_bytes.find(sync_word)
    if sync_pos == -1:
        raise ValueError("Sync word not found in bitstream!")

    payload_start = sync_pos + len(sync_word)
    length = raw_bytes[payload_start]
    payload = raw_bytes[payload_start + 1 : payload_start + 1 + length]
    rx_crc = int.from_bytes(raw_bytes[payload_start + 1 + length : payload_start + 1 + length + 2], "big")

    # Verify CRC
    calc_crc = crc16_ccitt(raw_bytes[payload_start : payload_start + 1 + length])
    if calc_crc != rx_crc:
        print(f"[!] Warning: CRC mismatch: calc={calc_crc:04x} rx={rx_crc:04x}")
    else:
        print(f"[+] CRC-16 CCITT verified: 0x{calc_crc:04x}")

    flag = payload.decode("ascii")
    print(f"[+] Flag: {flag}")
    return flag

if __name__ == "__main__":
    solve()
