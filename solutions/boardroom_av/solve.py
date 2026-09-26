"""
Boardroom AV Challenge Solver
Author: Antigravity
Flag: H7CTF{2fb1aabd-652b-4ff7-b700-2af47886108e}

Description:
1. Downloads the HLS stream playlist /boardroom/index.m3u8 and its .ts segments from the target host.
2. Concatenates the MPEG-TS segments and decodes the audio stream using PyAV.
3. Detects the 1.67s AFSK burst situated around 2.0s - 3.7s.
4. Demodulates the Bell 202 tones (1200 Hz Mark, 2200 Hz Space) at 300 baud (UART 8N1).
5. Recovers the flag: H7CTF{2fb1aabd-652b-4ff7-b700-2af47886108e}.
"""

import os
import re
import ssl
import sys
import urllib.request
import av
import numpy as np
from scipy.signal import butter, filtfilt, hilbert

HOST = 'web-17e4256823c5a05c.web.h7tex.com'
BASE_URL = f'https://{HOST}/boardroom/'

def solve():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("[*] Fetching /boardroom/index.m3u8 ...")
    req = urllib.request.Request(BASE_URL + 'index.m3u8', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        playlist = resp.read().decode('utf-8')
    except Exception as e:
        print(f"[-] Network fetch failed ({e}), checking local cache...")
        playlist = None

    ts_data = b""
    local_combined = 'solutions/boardroom_av/combined.ts'

    if playlist:
        segments = [line.strip() for line in playlist.splitlines() if line.strip().endswith('.ts')]
        print(f"[*] Found {len(segments)} segments in playlist")
        for seg in segments:
            seg_url = BASE_URL + seg
            r = urllib.request.Request(seg_url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(r, context=ctx, timeout=10).read()
            ts_data += data
    elif os.path.exists(local_combined):
        print(f"[*] Using local {local_combined}")
        with open(local_combined, 'rb') as f:
            ts_data = f.read()
    else:
        raise RuntimeError("No TS data available")

    # Decode audio using PyAV
    import io
    container = av.open(io.BytesIO(ts_data), format='mpegts')
    audio_frames = []
    sr = 48000
    for frame in container.decode(audio=0):
        sr = frame.sample_rate
        audio_frames.append(frame.to_ndarray())
    container.close()

    audio = np.concatenate(audio_frames, axis=-1)[0].astype(np.float64)
    print(f"[*] Decoded audio: {len(audio)} samples @ {sr} Hz ({len(audio)/sr:.2f}s)")

    # Find the high-energy burst region
    thresh = 0.2 * np.max(np.abs(audio))
    burst_idx = np.where(np.abs(audio) > thresh)[0]
    if len(burst_idx) == 0:
        raise RuntimeError("Could not find audio burst")

    start_idx = burst_idx[0]
    end_idx = burst_idx[-1]
    burst = audio[start_idx:end_idx + 1]
    burst = burst / np.max(np.abs(burst))
    print(f"[*] Located burst: samples {start_idx} to {end_idx} ({len(burst)/sr:.3f}s)")

    # Bandpass filter for Bell 202 frequencies (1000 - 2400 Hz)
    b_bp, a_bp = butter(4, [1000 / (sr / 2), 2400 / (sr / 2)], btype='band')
    filtered = filtfilt(b_bp, a_bp, burst)

    # FM discriminator via instantaneous frequency of analytic signal
    analytic = hilbert(filtered)
    inst_freq = np.diff(np.unwrap(np.angle(analytic))) * sr / (2 * np.pi)

    # Low-pass filter for symbol rate
    b_lp, a_lp = butter(4, 600 / (sr / 2), btype='low')
    smooth_freq = filtfilt(b_lp, a_lp, inst_freq)

    # Center frequency between Mark (1200 Hz) and Space (2200 Hz) is 1700 Hz
    freq_dev = smooth_freq - 1700.0

    # Demodulate at 300 baud
    baud = 300.0
    spb = sr / baud  # 160 samples per bit

    found_flag = None
    for offset in range(0, int(spb), 8):
        sample_indices = (np.arange(0, len(freq_dev), spb) + offset).astype(int)
        sample_indices = sample_indices[sample_indices < len(freq_dev)]
        bits = (freq_dev[sample_indices] < 0).astype(int)  # 1 for Mark (<1700 Hz), 0 for Space (>1700 Hz)

        # Parse UART 8N1: start bit = 0, 8 data bits (LSB first), stop bit = 1
        i = 0
        decoded_bytes = []
        while i + 10 <= len(bits):
            if bits[i] == 0:  # Start bit
                if bits[i + 9] == 1:  # Stop bit
                    val = sum(bits[i + 1 + k] << k for k in range(8))
                    decoded_bytes.append(val)
                    i += 10
                    continue
            i += 1

        text = bytes(decoded_bytes)
        m = re.search(rb'H7CTF\{[0-9a-f\-]{36}\}', text)
        if m:
            found_flag = m.group(0).decode('ascii')
            break

    if found_flag:
        print(f"[+] Flag: {found_flag}")
        return found_flag
    else:
        raise RuntimeError("Flag not recovered from AFSK signal")

if __name__ == '__main__':
    solve()
