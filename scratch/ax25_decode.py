import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, filtfilt, hilbert

sr, data = wavfile.read('solutions/boardroom_av/boardroom.wav')
burst = data[97025:177344].astype(float)
burst = burst / np.max(np.abs(burst))

# Bandpass filter around 1000 - 2400 Hz
b_bp, a_bp = butter(4, [1000 / (sr/2), 2400 / (sr/2)], btype='band')
filtered = filtfilt(b_bp, a_bp, burst)

analytic = hilbert(filtered)
inst_phase = np.unwrap(np.angle(analytic))
inst_freq = np.diff(inst_phase) * sr / (2 * np.pi)

b_lp, a_lp = butter(4, 1200 / (sr/2), btype='low')
smooth_freq = filtfilt(b_lp, a_lp, inst_freq)

freq_deviation = smooth_freq - 1700.0
baud = 1200.0
spb = sr / baud

offset = 38
sample_indices = np.arange(offset, len(freq_deviation), int(spb))
bits = (freq_deviation[sample_indices] < 0).astype(int)

# NRZI decoding
nrzi = [1 if bits[i] == bits[i-1] else 0 for i in range(1, len(bits))]

# HDLC frame decoding
# In HDLC:
# Flags are 01111110 (0x7E)
# Between flags: bit stuffing (0 inserted after five consecutive 1s)
# Each byte is transmitted LSB first

def decode_hdlc_frames(bitstream):
    flag = [0, 1, 1, 1, 1, 1, 1, 0]
    
    # State machine to find frames
    frames = []
    current_frame_bits = []
    ones_count = 0
    in_frame = False
    
    i = 0
    while i < len(bitstream):
        # Check for flag pattern
        if i + 8 <= len(bitstream) and bitstream[i:i+8] == flag:
            if in_frame and len(current_frame_bits) >= 16:
                frames.append(current_frame_bits)
                current_frame_bits = []
            in_frame = True
            i += 8
            ones_count = 0
            continue
        
        if in_frame:
            bit = bitstream[i]
            if ones_count == 5:
                if bit == 0:
                    # Stuffed bit: drop it!
                    ones_count = 0
                    i += 1
                    continue
                else:
                    # 6 or more 1s (invalid or abort)
                    in_frame = False
                    current_frame_bits = []
                    ones_count = 0
                    i += 1
                    continue
            
            current_frame_bits.append(bit)
            if bit == 1:
                ones_count += 1
            else:
                ones_count = 0
        i += 1
        
    return frames

frames = decode_hdlc_frames(nrzi)
print(f"Total HDLC frames extracted: {len(frames)}")

for f_idx, frame_bits in enumerate(frames):
    print(f"\n--- Frame {f_idx} ({len(frame_bits)} bits) ---")
    # Convert to bytes (LSB first)
    byte_vals = []
    for j in range(0, len(frame_bits) - 7, 8):
        byte_val = sum(frame_bits[j+k] << k for k in range(8))
        byte_vals.append(byte_val)
    
    data_bytes = bytes(byte_vals)
    print("Raw hex:", data_bytes.hex())
    print("Raw bytes:", data_bytes)
    
    # AX.25 address fields are shifted left by 1 bit!
    # Destination (7 bytes), Source (7 bytes), Control (1 byte), PID (1 byte), Info (N bytes), FCS (2 bytes)
    if len(data_bytes) >= 16:
        dest = "".join(chr(b >> 1) for b in data_bytes[0:6])
        src = "".join(chr(b >> 1) for b in data_bytes[7:13])
        control = data_bytes[14]
        pid = data_bytes[15]
        info = data_bytes[16:-2]
        fcs = data_bytes[-2:]
        print(f"AX.25 Dest: {dest.strip()}, Src: {src.strip()}, Control: {control:#04x}, PID: {pid:#04x}")
        print("Info field hex:", info.hex())
        print("Info field text:", repr(info))
        if b"H7CTF" in info:
            print("\n[!!!] FLAG FOUND IN INFO FIELD:", info.decode(errors='replace'))
