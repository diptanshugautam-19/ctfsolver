import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, filtfilt

# Load audio
sr, data = wavfile.read('solutions/boardroom_av/boardroom.wav')
burst = data[97025:177344].astype(float)
burst = burst / np.max(np.abs(burst))

# Bell 202 parameters
f_mark = 1200.0   # 1200 Hz (often binary 1)
f_space = 2200.0  # 2200 Hz (often binary 0)
baud = 1200.0
samples_per_bit = sr / baud  # 40.0 samples

print(f"Sample rate: {sr}, baud: {baud}, samples_per_bit: {samples_per_bit}")

# Demodulation via Goertzel or correlation over symbol window
# Let's correlate with 1200 Hz and 2200 Hz
t = np.arange(len(burst)) / sr
ref_1200_cos = np.cos(2 * np.pi * f_mark * t)
ref_1200_sin = np.sin(2 * np.pi * f_mark * t)
ref_2200_cos = np.cos(2 * np.pi * f_space * t)
ref_2200_sin = np.sin(2 * np.pi * f_space * t)

# Multiply
m_cos = burst * ref_1200_cos
m_sin = burst * ref_1200_sin
s_cos = burst * ref_2200_cos
s_sin = burst * ref_2200_sin

# Low pass filter (moving average of 40 samples, or butterworth LP at ~1200 Hz)
nyq = sr / 2
b_lp, a_lp = butter(4, 1200 / nyq, btype='low')

m_cos_f = filtfilt(b_lp, a_lp, m_cos)
m_sin_f = filtfilt(b_lp, a_lp, m_sin)
s_cos_f = filtfilt(b_lp, a_lp, s_cos)
s_sin_f = filtfilt(b_lp, a_lp, s_sin)

energy_mark = m_cos_f**2 + m_sin_f**2
energy_space = s_cos_f**2 + s_sin_f**2

diff = energy_mark - energy_space

# Find optimal sampling offset (phase within the 40-sample symbol)
# During the preamble, diff should be strongly positive (mark).
# When transitions start, diff fluctuates.
total_bits = int(len(burst) / samples_per_bit)
print(f"Total bits: {total_bits}")

for sample_offset in range(0, int(samples_per_bit), 2):
    sample_points = (np.arange(total_bits) * samples_per_bit + sample_offset).astype(int)
    sample_points = sample_points[sample_points < len(diff)]
    
    # 1 if mark > space else 0
    raw_bits = (diff[sample_points] > 0).astype(int)
    
    # Check 1: Direct UART 8N1 (LSB first or MSB first)
    # Check 2: Inverted UART 8N1
    # Check 3: NRZI (AX.25 packet radio: 0 = transition, 1 = no transition)
    
    for invert in [False, True]:
        b = 1 - raw_bits if invert else raw_bits
        
        # Test NRZI decoding:
        # in NRZI: bit[i] = 1 if b[i] == b[i-1] else 0
        nrzi_bits = []
        for i in range(1, len(b)):
            nrzi_bits.append(1 if b[i] == b[i-1] else 0)
        
        # Search for HDLC flag 01111110 (0x7E) in nrzi_bits
        nrzi_str = "".join(map(str, nrzi_bits))
        if "01111110" in nrzi_str:
            print(f"Offset {sample_offset}, invert={invert}: Found HDLC flag in NRZI!")
            # Let's un-bit-stuff and decode AX.25
            # In AX.25, after 5 consecutive 1s, a 0 is stuffed and must be dropped.
            # Flags are 01111110 (no bit stuffing in flag).
            # Let's inspect!
            
        # Test UART 8N1 (look for H7CTF):
        # Start bit = 0, 8 data bits, Stop bit = 1
        # Test all bit shifts
        for bit_shift in range(10):
            chars_lsb = []
            chars_msb = []
            i = bit_shift
            while i + 10 <= len(b):
                start_bit = b[i]
                data_bits = b[i+1:i+9]
                stop_bit = b[i+9]
                # If start_bit == 0 and stop_bit == 1:
                val_lsb = sum(data_bits[k] << k for k in range(8))
                val_msb = sum(data_bits[k] << (7 - k) for k in range(8))
                chars_lsb.append(val_lsb)
                chars_msb.append(val_msb)
                i += 10
            
            txt_lsb = bytes(chars_lsb)
            txt_msb = bytes(chars_msb)
            if b"H7CTF" in txt_lsb or b"h7ctf" in txt_lsb or b"flag" in txt_lsb:
                print(f"[!] FOUND IN UART LSB! Offset {sample_offset}, shift {bit_shift}, invert {invert}: {txt_lsb}")
            if b"H7CTF" in txt_msb or b"h7ctf" in txt_msb or b"flag" in txt_msb:
                print(f"[!] FOUND IN UART MSB! Offset {sample_offset}, shift {bit_shift}, invert {invert}: {txt_msb}")
