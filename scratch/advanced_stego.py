import av
import numpy as np
from scipy import signal
from scipy.fft import fft, rfft, rfftfreq
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
# 1. High-resolution spectrogram for visual flag inspection
# ============================================================
print("\n=== High-resolution spectrogram ===")
# Use small window for good time resolution
nperseg = 512
freqs, times, Sxx = signal.spectrogram(audio, fs=sr, nperseg=nperseg, noverlap=480)
print(f"Spectrogram: {Sxx.shape} - freqs up to {freqs[-1]:.0f}Hz, {len(times)} time bins")

# Check specific bands for patterns
# If there's a hidden message, it might appear in a specific freq range
# Print text representation of spectrogram at key frequencies

# Focus on "unusual" frequency bands 
print("\nSpectrogram in 18kHz-24kHz (near Nyquist):")
hi_mask = (freqs >= 18000) & (freqs <= 24000)
hi_sxx = Sxx[hi_mask]
hi_freqs = freqs[hi_mask]
if hi_sxx.max() > 0:
    hi_norm = (hi_sxx - hi_sxx.min()) / (hi_sxx.max() - hi_sxx.min() + 1e-12)
    chars = ' .:-=+*#@'
    for fi, f in enumerate(hi_freqs[::2]):
        row = ''.join(chars[min(int(v * (len(chars)-1)), len(chars)-1)] for v in hi_norm[fi*2, :])
        print(f"  {f:.0f}Hz: {row}")

# ============================================================
# 2. Phase encoding detection
# ============================================================
print("\n=== Phase Analysis ===")
# Split into small blocks and measure phase
block_size = sr // 100  # 10ms blocks
num_blocks = len(audio) // block_size
print(f"Analyzing {num_blocks} blocks of {block_size} samples each")

# Check for phase jumps (PSK-like encoding)
phase_values = []
for i in range(num_blocks):
    block = audio[i*block_size:(i+1)*block_size]
    # Get dominant frequency phase
    spec = rfft(block)
    mag = np.abs(spec)
    if mag.max() > 0:
        peak_idx = np.argmax(mag)
        phase = np.angle(spec[peak_idx])
        phase_values.append(phase)

print(f"Phase values (first 20): {[f'{p:.2f}' for p in phase_values[:20]]}")

# ============================================================  
# 3. Try known audio steganography tools - Steghide signature
# ============================================================
print("\n=== Checking for steganography tool signatures ===")
wav_file = f'{out_dir}/boardroom.wav'
with open(wav_file, 'rb') as f:
    wav_data = f.read()

# Check for steghide magic
steghide_magic = b'steghide'
if steghide_magic in wav_data:
    print("  [!] Steghide magic found!")
    
# Check for SilentEye, OpenStego, DeepSound signatures
for sig, name in [
    (b'RIFF', 'WAV header'),
    (b'OpenStego', 'OpenStego'),
    (b'SilentEye', 'SilentEye'),
    (b'DeepSound', 'DeepSound'),
    (b'WavSteg', 'WavSteg'),
    (b'\x53\x74\x65\x67', 'Steg?'),
]:
    if sig in wav_data:
        idx = wav_data.index(sig)
        print(f"  Found '{name}' at offset {idx}")

# ============================================================
# 4. Frequency analysis: check if specific tone pairs encode data
# ============================================================
print("\n=== Tone-based encoding detection ===")
# The spectrogram showed high energy at ~1125Hz and ~2250Hz (double)
# This might be a single-tone encoding scheme (FSK)

# Analyze energy in specific frequency bands over time
target_freqs = [1000, 1125, 1250, 2000, 2250, 2500, 440, 880, 1760]
for tf in target_freqs:
    # Find closest bin
    idx = np.argmin(np.abs(freqs - tf))
    energy_over_time = Sxx[idx, :]
    mean_e = energy_over_time.mean()
    max_e = energy_over_time.max()
    std_e = energy_over_time.std()
    if max_e > 0.001:
        print(f"  {tf}Hz: mean={mean_e:.6f}, max={max_e:.6f}, std={std_e:.6f} -- {'ACTIVE' if max_e > mean_e*3 else 'flat'}")

# ============================================================
# 5. OOK (On-Off Keying) / amplitude modulation detection
# ============================================================
print("\n=== OOK / Amplitude Modulation Detection ===")
# Bandpass filter at suspicious frequencies
from scipy.signal import butter, filtfilt

def bandpass(data, low, high, fs, order=4):
    nyq = fs / 2
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, data)

for center, bw in [(1125, 100), (2250, 100), (440, 50), (1000, 100)]:
    try:
        filtered = bandpass(audio, center-bw, center+bw, sr)
        envelope = np.abs(signal.hilbert(filtered))
        # Downsample envelope
        dec_factor = 480  # 100Hz output
        env_ds = envelope[::dec_factor]
        # Detect threshold crossings
        thresh = envelope.mean() * 2
        bits = (env_ds > thresh).astype(int)
        nonzero = bits.sum()
        if nonzero > 0:
            print(f"  {center}Hz band: {nonzero}/{len(bits)} ON bits")
            # Decode as bits
            if 8 <= len(bits) <= 500:
                byte_data = bytearray()
                for j in range(0, len(bits)-7, 8):
                    byte_val = sum(bits[j+k] << (7-k) for k in range(8))
                    byte_data.append(byte_val)
                printable = bytes([b for b in byte_data if 32 <= b < 127])
                if len(printable) > 4:
                    print(f"    Decoded text: {printable}")
                for m in re.finditer(b'H7CTF', byte_data):
                    print(f"    [FLAG!] {byte_data[m.start():m.start()+50]}")
    except Exception as e:
        print(f"  {center}Hz: error {e}")

# ============================================================
# 6. Check if audio data decoded to PCM has patterns
# ============================================================
print("\n=== PCM Sample Pattern Analysis ===")
# Convert to int16 range
samples_int = (audio * 32768).astype(np.int16)

# Check sample values: look for repeating bit patterns
# Extract every Nth bit as a stream
for n in [1, 2, 3, 4, 8, 16]:
    extracted = []
    for s in samples_int[:1000]:
        extracted.append((int(s) >> n) & 0xFF)
    unique = len(set(extracted))
    if unique < 20:
        print(f"  Bit position {n}: only {unique} unique values: {set(list(extracted)[:50])}")

# ============================================================
# 7. Check for N-LSB steganography with PyAV exact float values
# ============================================================
print("\n=== Float LSB Analysis ===")
# AAC is in float planar format. The actual float values might have hidden bits
# after the precision that audio quantization would use

# AAC is lossy, but if someone embedded data by manipulating the float values
# of the decoded audio...

# Convert floats to binary representation
import struct
float_bits = []
for f in audio[:1000]:
    bits = struct.pack('>f', float(f))
    for b in bits:
        for i in range(8):
            float_bits.append((b >> (7-i)) & 1)

# Extract LSBs of the float mantissa (last 8 bits of 23-bit mantissa)
float_lsb = []
for f in audio:
    bits = struct.pack('>f', float(f))
    int_val = struct.unpack('>I', bits)[0]
    # Last 8 bits of mantissa
    float_lsb.append(int_val & 0xFF)

float_lsb_bytes = bytes(float_lsb)
print(f"Float LSBs (first 50): {float_lsb_bytes[:50].hex()}")

for m in re.finditer(b'H7CTF', float_lsb_bytes):
    print(f"  [FLAG in float LSBs!] {float_lsb_bytes[m.start():m.start()+50]}")

# Check if float LSBs are unusually uniform/patterned
unique_lsb = len(set(float_lsb))
print(f"Unique float LSB values: {unique_lsb}/256")

print("\nDone.")
