#!/usr/bin/env python3
"""
H7CTF - Rolling-Code Garage Remote Solver
Demodulates raw complex baseband I/Q (OOK / PWM), parses 8 captured 48-bit frames,
recovers the rolling code generation rule, computes the 9th code, and submits to unlock.
"""

import sys
import os
import json
import urllib.request
import numpy as np

CHALLENGE_URL = "https://web-ae0648197b3162a2.web.h7tex.com"
CAPTURE_FILE = "capture.cf32"

def ensure_capture():
    if not os.path.exists(CAPTURE_FILE):
        print(f"[+] Downloading {CAPTURE_FILE} from {CHALLENGE_URL}...")
        urllib.request.urlretrieve(f"{CHALLENGE_URL}/{CAPTURE_FILE}", CAPTURE_FILE)
    print(f"[+] Using {CAPTURE_FILE} ({os.path.getsize(CAPTURE_FILE)} bytes)")

def demodulate_and_parse():
    print("[+] Loading complex baseband samples...")
    raw = np.fromfile(CAPTURE_FILE, dtype=np.complex64)
    mag = np.abs(raw)
    high = (mag > 0.5).astype(int)

    # Run-length transitions
    diff = np.diff(high)
    trans = np.where(diff != 0)[0]

    runs = []
    for i in range(len(trans) - 1):
        state = high[trans[i] + 1]
        length = trans[i+1] - trans[i]
        runs.append((state, length))

    # Split into frames by inter-frame gap (>1500 samples of LOW)
    frames = []
    curr = []
    for i in range(len(runs)):
        state, length = runs[i]
        if state == 1:
            low_len = runs[i+1][1] if i + 1 < len(runs) else 0
            curr.append((length, low_len))
            if low_len > 1500:
                frames.append(curr)
                curr = []
    if curr:
        frames.append(curr)

    print(f"[+] Detected {len(frames)} frames in capture.")

    # 48 bits per frame with PWM: 300us = 0, 600us = 1
    codes = []
    for idx, f in enumerate(frames):
        # 48 data pulses + 1 trailing pulse
        bits = [1 if p[0] > 450 else 0 for p in f[:48]]
        hex_code = f"{int(''.join(str(b) for b in bits), 2):012x}"
        codes.append(hex_code)
        print(f"    Frame {idx}: {hex_code}")

    return codes

def predict_next(codes):
    print("[+] Analyzing code progression...")
    # Verify fixed 32-bit prefix
    prefix = codes[0][:8]
    assert all(c.startswith(prefix) for c in codes), "Prefix mismatch!"

    # Byte 4 (indices 8:10 in hex)
    b4_vals = [int(c[8:10], 16) for c in codes]
    diffs = [b4_vals[i+1] - b4_vals[i] for i in range(len(b4_vals)-1)]
    assert all(d == 7 for d in diffs), f"Non-constant byte 4 delta: {diffs}"
    next_b4 = b4_vals[-1] + 7

    # Checksum / last byte verification
    # Last nibble follows (7*k mod 15) + 1 or sum(first 10 nibbles) - 56
    next_nibbles_prefix = [int(c, 16) for c in prefix]
    next_nibbles_b4 = [next_b4 >> 4, next_b4 & 0xF]
    sum10 = sum(next_nibbles_prefix) + sum(next_nibbles_b4)
    next_last_nib = sum10 - 56
    next_b5 = 0x80 | (next_last_nib & 0x0F)

    next_code = f"{prefix}{next_b4:02x}{next_b5:02x}"
    print(f"[+] Predicted next frame (Frame {len(codes)}): {next_code}")
    return next_code

def unlock(code):
    print(f"[+] Submitting {code} to {CHALLENGE_URL}/unlock...")
    req = urllib.request.Request(
        f"{CHALLENGE_URL}/unlock",
        data=json.dumps({"code": code}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    print(f"[+] Server response: {data}")
    flag = data.get("flag")
    if flag:
        print(f"[SUCCESS] Flag recovered: {flag}")
        return flag
    else:
        raise RuntimeError(f"Unlock failed: {data}")

def main():
    ensure_capture()
    codes = demodulate_and_parse()
    next_code = predict_next(codes)
    flag = unlock(next_code)
    print(f"\nFinal Flag: {flag}")

if __name__ == "__main__":
    main()
