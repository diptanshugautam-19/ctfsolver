import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, filtfilt

sr, data = wavfile.read('solutions/boardroom_av/boardroom.wav')
burst = data[97025:177344].astype(float)
burst = burst / np.max(np.abs(burst))

f_mark = 1200.0
f_space = 2200.0
baud = 1200.0
samples_per_bit = sr / baud

t = np.arange(len(burst)) / sr
m_cos = filtfilt(*butter(4, 1200 / (sr/2), btype='low'), burst * np.cos(2 * np.pi * f_mark * t))
m_sin = filtfilt(*butter(4, 1200 / (sr/2), btype='low'), burst * np.sin(2 * np.pi * f_mark * t))
s_cos = filtfilt(*butter(4, 1200 / (sr/2), btype='low'), burst * np.cos(2 * np.pi * f_space * t))
s_sin = filtfilt(*butter(4, 1200 / (sr/2), btype='low'), burst * np.sin(2 * np.pi * f_space * t))

diff = (m_cos**2 + m_sin**2) - (s_cos**2 + s_sin**2)

# Let's inspect around offset 36 (34, 35, 36, 37, 38)
for sample_offset in [34, 35, 36, 37, 38]:
    total_bits = int(len(burst) / samples_per_bit)
    sample_points = (np.arange(total_bits) * samples_per_bit + sample_offset).astype(int)
    sample_points = sample_points[sample_points < len(diff)]
    
    raw_bits = (diff[sample_points] > 0).astype(int)
    
    # NRZI decoding
    # In NRZI: 0 = transition, 1 = no transition
    nrzi = [1 if raw_bits[i] == raw_bits[i-1] else 0 for i in range(1, len(raw_bits))]
    
    # Let's find all occurrences of 01111110
    bit_str = "".join(map(str, nrzi))
    print(f"\nOffset {sample_offset}:")
    
    # Find all flag positions
    flag = "01111110"
    pos = 0
    flag_indices = []
    while True:
        idx = bit_str.find(flag, pos)
        if idx == -1:
            break
        flag_indices.append(idx)
        pos = idx + 1
    print(f"Flag indices ({len(flag_indices)}):", flag_indices)
    
    # Unstuff bits between flags or after the opening flags
    # In HDLC, opening flags can be back-to-back: 0111111001111110...
    # After consecutive flags end, the payload begins!
    if len(flag_indices) >= 2:
        # Let's examine chunks between first flag and last flag
        start_idx = flag_indices[0] + 8
        end_idx = flag_indices[-1]
        
        # Unstuff bits: remove '0' after five consecutive '1's
        sub_bits = nrzi[start_idx:end_idx]
        unstuffed = []
        ones_count = 0
        for bit in sub_bits:
            if ones_count == 5:
                if bit == 0:
                    # Stuffed bit! Drop it.
                    ones_count = 0
                    continue
                elif bit == 1:
                    # Flag or error!
                    ones_count = 0
                    # if it's a flag, reset
                    continue
            unstuffed.append(bit)
            if bit == 1:
                ones_count += 1
            else:
                ones_count = 0
        
        # Convert unstuffed bits to bytes (LSB first in HDLC/AX.25!)
        bytes_lsb = bytearray()
        for i in range(0, len(unstuffed) - 7, 8):
            bval = sum(unstuffed[i+k] << k for k in range(8))
            bytes_lsb.append(bval)
            
        bytes_msb = bytearray()
        for i in range(0, len(unstuffed) - 7, 8):
            bval = sum(unstuffed[i+k] << (7-k) for k in range(8))
            bytes_msb.append(bval)
            
        print("LSB bytes:", bytes_lsb)
        print("MSB bytes:", bytes_msb)
        if b"H7CTF" in bytes_lsb:
            print("[!!!] FLAG FOUND IN LSB:", bytes_lsb)
        if b"H7CTF" in bytes_msb:
            print("[!!!] FLAG FOUND IN MSB:", bytes_msb)
