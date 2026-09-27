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
b_lp, a_lp = butter(4, 600 / (sr/2), btype='low')
smooth_freq = filtfilt(b_lp, a_lp, inst_freq)
freq_deviation = smooth_freq - 1700.0

baud = 300.0
spb = sr / baud # 160.0 samples per bit!

print(f"Baud: {baud}, samples per bit: {spb}")

for offset in range(0, 160, 8):
    sample_indices = (np.arange(0, len(freq_deviation), spb) + offset).astype(int)
    sample_indices = sample_indices[sample_indices < len(freq_deviation)]
    
    # Check both polarities:
    # Standard: Mark (1200) = 1, Space (2200) = 0
    # Inverted: Mark (1200) = 0, Space (2200) = 1
    for invert in [False, True]:
        if not invert:
            bits = (freq_deviation[sample_indices] < 0).astype(int) # 1 if < 1700 (Mark)
        else:
            bits = (freq_deviation[sample_indices] > 0).astype(int)
            
        bit_str = "".join(map(str, bits))
        
        # Test UART 8N1: Idle is 1 (Mark).
        # Start bit is 0 (Space).
        # 8 Data bits (usually LSB first).
        # Stop bit is 1 (Mark).
        
        # Frame parser: scan for start bit
        i = 0
        decoded_chars = []
        while i + 10 <= len(bits):
            if bits[i] == 0: # Start bit
                # Check stop bit
                if bits[i+9] == 1: # Valid stop bit!
                    byte_bits = bits[i+1:i+9]
                    # LSB first
                    val = sum(byte_bits[k] << k for k in range(8))
                    decoded_chars.append((i, val))
                    i += 10 # Move to next frame
                    continue
            i += 1
            
        text = bytes([c[1] for c in decoded_chars])
        if b"H7CTF" in text or b"h7ctf" in text or b"flag" in text or len([c for c in text if 32 <= c < 127]) > 10:
            print(f"\nOffset {offset}, invert={invert}:")
            print("Decoded text:", text)
            print("String repr:", text.decode(errors='replace'))
