import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, filtfilt, hilbert

sr, data = wavfile.read('solutions/boardroom_av/boardroom.wav')
burst = data[97025:177344].astype(float)
burst = burst / np.max(np.abs(burst))

b_bp, a_bp = butter(4, [1000 / (sr/2), 2400 / (sr/2)], btype='band')
filtered = filtfilt(b_bp, a_bp, burst)
analytic = hilbert(filtered)
inst_freq = np.diff(np.unwrap(np.angle(analytic))) * sr / (2 * np.pi)
b_lp, a_lp = butter(4, 1200 / (sr/2), btype='low')
smooth_freq = filtfilt(b_lp, a_lp, inst_freq)
freq_deviation = smooth_freq - 1700.0

baud = 1200.0
spb = sr / baud

def parse_hdlc(nrzi_bits):
    frames = []
    current_bits = []
    ones = 0
    
    i = 0
    while i < len(nrzi_bits):
        b = nrzi_bits[i]
        if b == 1:
            ones += 1
            current_bits.append(1)
            i += 1
        else: # b == 0
            if ones == 5:
                # Bit stuffing: 0 inserted after five 1s. Drop the 0!
                current_bits.pop() # Wait, the five 1s are kept, the 0 is stuffed!
                # Wait: in current_bits, we already have the five 1s. We just DON'T append this 0.
                ones = 0
                i += 1
            elif ones == 6:
                # 01111110: This is a FLAG!
                # Remove the six 1s that were just appended
                frame_data = current_bits[:-6]
                if len(frame_data) >= 16: # At least 2 bytes
                    frames.append(frame_data)
                current_bits = []
                ones = 0
                i += 1
            elif ones >= 7:
                # Abort
                current_bits = []
                ones = 0
                i += 1
            else:
                current_bits.append(0)
                ones = 0
                i += 1
    return frames

for offset in range(35, 40):
    sample_indices = np.arange(offset, len(freq_deviation), int(spb))
    bits = (freq_deviation[sample_indices] < 0).astype(int)
    nrzi = [1 if bits[i] == bits[i-1] else 0 for i in range(1, len(bits))]
    
    frames = parse_hdlc(nrzi)
    print(f"\n================ Offset {offset}: {len(frames)} frames found ================")
    for idx, f in enumerate(frames):
        # Convert to bytes (LSB first)
        bytelist = []
        for j in range(0, len(f) - 7, 8):
            val = sum(f[j+k] << k for k in range(8))
            bytelist.append(val)
        raw_b = bytes(bytelist)
        print(f"Frame {idx} ({len(f)} bits, {len(raw_b)} bytes): {raw_b}")
        if b"H7CTF" in raw_b or b"h7ctf" in raw_b or b"{" in raw_b:
            print(f"[!!!] FLAG FOUND: {raw_b}")
            
        # Also check MSB first
        bytelist_msb = []
        for j in range(0, len(f) - 7, 8):
            val = sum(f[j+k] << (7-k) for k in range(8))
            bytelist_msb.append(val)
        raw_msb = bytes(bytelist_msb)
        if b"H7CTF" in raw_msb or b"h7ctf" in raw_msb or b"{" in raw_msb:
            print(f"[!!!] FLAG FOUND IN MSB: {raw_msb}")
