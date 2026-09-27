import av
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
import struct
import re

out_dir = 'solutions/boardroom_av'
ts_file = f'{out_dir}/combined.ts'

# Decode audio
container = av.open(ts_file)
all_samples = []
sr = 48000
for frame in container.decode(audio=0):
    sr = frame.sample_rate
    arr = frame.to_ndarray()
    all_samples.append(arr)
container.close()

audio = np.concatenate(all_samples, axis=-1)[0].astype(np.float64)
print(f"Audio: {len(audio)} samples, {sr}Hz, {len(audio)/sr:.2f}s")

# ============================================================
# Phase values analysis - the phase data was highly binary!
# Phase ~π (3.14) = binary 1, Phase ~0 = binary 0
# ============================================================

def decode_phase_as_bpsk(audio, sr, block_size_ms=10):
    """Decode phase-encoded data using BPSK"""
    block_size = int(sr * block_size_ms / 1000)
    num_blocks = len(audio) // block_size
    
    bits = []
    phases = []
    
    for i in range(num_blocks):
        block = audio[i*block_size:(i+1)*block_size]
        spec = rfft(block)
        mag = np.abs(spec)
        if mag.max() > 0:
            peak_idx = np.argmax(mag)
            phase = np.angle(spec[peak_idx])
            phases.append(phase)
            # Binary: |phase| > π/2 → 1, else → 0
            bits.append(1 if abs(phase) > np.pi/2 else 0)
    
    return bits, phases

# Try different block sizes to find the right carrier
print("=== BPSK decoding at different block sizes ===")
for block_ms in [10, 20, 5, 1, 2]:
    bits, phases = decode_phase_as_bpsk(audio, sr, block_ms)
    print(f"\n  Block {block_ms}ms: {len(bits)} bits")
    
    # Convert to bytes (MSB first)
    byte_data = bytearray()
    for j in range(0, len(bits)-7, 8):
        bval = sum(bits[j+k] << (7-k) for k in range(8))
        byte_data.append(bval)
    
    print(f"  Bits (first 32): {bits[:32]}")
    print(f"  Bytes hex: {byte_data[:30].hex()}")
    
    # Look for flag
    for m in re.finditer(b'H7CTF', bytes(byte_data)):
        end = bytes(byte_data).index(b'}', m.start()) + 1
        print(f"  [FLAG!] {bytes(byte_data[m.start():end]).decode()}")
    
    # Look for printable text
    text = ''
    for b in byte_data:
        if 32 <= b < 127:
            text += chr(b)
        else:
            if len(text) >= 5:
                print(f"  Text: {text}")
            text = ''

# ============================================================
# Look more carefully at the OOK bands
# ============================================================
print("\n=== Detailed OOK analysis at active bands ===")

def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = fs / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

# The OOK bands showed activity at 1125Hz, 2250Hz, 440Hz, 1000Hz
# Let's do proper FSK/OOK demodulation

for center_freq, bw in [(1125, 50), (2250, 50), (440, 30), (1000, 50)]:
    try:
        filtered = bandpass_filter(audio, center_freq - bw, center_freq + bw, sr)
        
        # Extract amplitude envelope
        from scipy.signal import hilbert
        analytic = hilbert(filtered)
        envelope = np.abs(analytic)
        
        # Apply low-pass filter to smooth the envelope
        from scipy.signal import butter, filtfilt
        nyq = sr / 2
        lp_cutoff = 50  # Hz - symbol rate is probably < 50 baud
        b, a = signal.butter(4, lp_cutoff / nyq, btype='low')
        envelope_smooth = signal.filtfilt(b, a, envelope)
        
        # Find threshold
        thresh = (envelope_smooth.max() + envelope_smooth.min()) / 2
        binary = (envelope_smooth > thresh).astype(int)
        
        # Find transitions
        transitions = np.diff(binary)
        trans_indices = np.where(transitions != 0)[0]
        
        print(f"\n  {center_freq}Hz: max={envelope.max():.4f}, mean={envelope.mean():.4f}")
        print(f"    Threshold: {thresh:.4f}, transitions: {len(trans_indices)}")
        
        if 5 < len(trans_indices) < 500:
            # Sample at midpoints
            segments = []
            for k in range(len(trans_indices)-1):
                mid = (trans_indices[k] + trans_indices[k+1]) // 2
                segments.append(binary[mid])
            
            print(f"    Segments: {segments[:40]}")
            
            # Convert to bytes
            byte_data = bytearray()
            for j in range(0, len(segments)-7, 8):
                bval = sum(segments[j+k] << (7-k) for k in range(8))
                byte_data.append(bval)
            
            print(f"    Bytes: {byte_data[:20].hex()}")
            for m in re.finditer(b'H7CTF', bytes(byte_data)):
                print(f"    [FLAG!] found at offset {m.start()}")
    except Exception as e:
        print(f"  {center_freq}Hz: error {e}")

# ============================================================
# Try steghide-compatible analysis
# Read actual samples as int16 and look at specific bit planes
# ============================================================
print("\n=== Bit plane analysis (int16) ===")
samples_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)

for bit_plane in range(16):
    plane = ((samples_int16.astype(np.int32) >> bit_plane) & 1).astype(np.uint8)
    
    # Convert to bytes
    byte_data = bytearray()
    for j in range(0, len(plane)-7, 8):
        bval = sum(int(plane[j+k]) << (7-k) for k in range(8))
        byte_data.append(bval)
    
    # Check for flag
    found = False
    for m in re.finditer(b'H7CTF', bytes(byte_data)):
        found = True
        print(f"  [FLAG!] Bit plane {bit_plane}: {bytes(byte_data[m.start():m.start()+50])}")
    
    if not found:
        # Check entropy  
        ones = plane.sum()
        print(f"  Bit plane {bit_plane}: {ones}/{len(plane)} ones ({100*ones/len(plane):.1f}%) - {'balanced' if 40 < 100*ones/len(plane) < 60 else 'SKEWED'}")

# ============================================================
# Phase difference between consecutive samples
# ============================================================
print("\n=== Inter-sample phase difference ===")
# Compute instantaneous frequency from analytic signal
analytic = signal.hilbert(audio)
inst_phase = np.unwrap(np.angle(analytic))
inst_freq = np.diff(inst_phase) * sr / (2 * np.pi)

print(f"Inst freq: mean={inst_freq.mean():.1f}Hz, std={inst_freq.std():.1f}Hz")
print(f"Inst freq range: [{inst_freq.min():.1f}, {inst_freq.max():.1f}]")

# Quantize to nearest 100Hz and see if there's a pattern
freq_quantized = np.round(inst_freq / 100) * 100
unique_freqs = np.unique(freq_quantized)
print(f"Quantized frequencies ({len(unique_freqs)} unique): {unique_freqs[:20]}")

# Check for FSK: alternating between two specific frequencies
# Find the two most common frequency values
from collections import Counter
freq_counts = Counter(freq_quantized.tolist())
top2 = freq_counts.most_common(5)
print(f"Most common quantized freqs: {top2}")

print("\nDone.")
