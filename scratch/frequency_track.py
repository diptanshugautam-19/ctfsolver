import av
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
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

# The spectrogram showed high energy at 1125Hz and 2250Hz bands
# And the FFT showed a strong 50Hz peak (possibly mains hum OR a carrier)
# Let's do a careful, high-resolution FFT

print("\n=== High-Resolution FFT ===")
fft_mag = np.abs(rfft(audio))
fft_freqs = rfftfreq(len(audio), 1/sr)

# Get top 50 peaks
from scipy.signal import find_peaks
peaks, props = find_peaks(fft_mag, height=np.max(fft_mag)*0.005, distance=5)
top_peaks = sorted(zip(fft_mag[peaks], fft_freqs[peaks]), reverse=True)[:50]

print("Top spectral components:")
for mag, freq in top_peaks[:30]:
    print(f"  {freq:8.2f} Hz: magnitude={mag:.2f}")

# ============================================================
# The audio probably has a hidden message as tones
# Let me try GOERTZEL algorithm for specific frequency detection
# over sliding windows to get precise timing
# ============================================================

def goertzel(samples, freq, sample_rate):
    """Compute energy at specific frequency using Goertzel algorithm"""
    N = len(samples)
    k = int(0.5 + N * freq / sample_rate)
    omega = 2.0 * np.pi * k / N
    coeff = 2.0 * np.cos(omega)
    s0, s1, s2 = 0.0, 0.0, 0.0
    for sample in samples:
        s0 = sample + coeff * s1 - s2
        s2 = s1
        s1 = s0
    power = s2**2 + s1**2 - coeff * s2 * s1
    return power

# Find exact dominant frequencies using sliding window
print("\n=== Sliding window frequency analysis ===")
window_ms = 50  # 50ms window
window = int(sr * window_ms / 1000)
step = window // 2
num_windows = (len(audio) - window) // step

# Check energy at top frequencies over time
check_freqs = [50, 1000, 1125, 1250, 2000, 2250, 2500, 440, 880, 100]

print(f"Window size: {window_ms}ms, Step: {window_ms/2}ms, Frames: {num_windows}")
print(f"Checking frequencies: {check_freqs}")

# Build energy matrix
energy_matrix = np.zeros((len(check_freqs), num_windows))
for w in range(num_windows):
    block = audio[w*step:w*step+window]
    for fi, freq in enumerate(check_freqs):
        energy_matrix[fi, w] = goertzel(block, freq, sr)

# Normalize
for fi in range(len(check_freqs)):
    if energy_matrix[fi].max() > 0:
        energy_matrix[fi] /= energy_matrix[fi].max()

print("\nEnergy over time (normalized, threshold 0.5):")
for fi, freq in enumerate(check_freqs):
    row = energy_matrix[fi]
    visual = ''.join('█' if v > 0.5 else '░' for v in row)
    mean = row.mean()
    print(f"  {freq:5.0f}Hz ({mean:.3f}): {visual}")

# ============================================================
# Try: the 50Hz dominant frequency is suspicious for 5.7 seconds
# of audio. Could be AC mains interference OR deliberate tone.
# Let's extract 50Hz tone energy precisely and see if it's modulated
# ============================================================
print("\n=== 50Hz tone modulation analysis ===")
# Bandpass around 50Hz
from scipy.signal import butter, filtfilt
nyq = sr / 2
b, a = butter(4, [40/nyq, 60/nyq], btype='band')
filtered_50hz = filtfilt(b, a, audio)

# Get envelope
from scipy.signal import hilbert
env_50hz = np.abs(hilbert(filtered_50hz))

# Downsample to see modulation
dec = 480  # ~100Hz output rate
env_ds = env_50hz[::dec]
times = np.arange(len(env_ds)) * dec / sr

print(f"50Hz envelope ({len(env_ds)} samples @ {sr/dec:.0f}Hz):")
# Threshold and binarize
thresh = env_ds.mean()
binary_50hz = (env_ds > thresh).astype(int)
print(f"  Envelope: {' '.join(f'{v:.3f}' for v in env_ds[:50])}")
print(f"  Binary:   {' '.join(str(b) for b in binary_50hz[:50])}")

# Convert to bits
bits_50hz = binary_50hz.tolist()
byte_data_50hz = bytearray()
for j in range(0, len(bits_50hz)-7, 8):
    bval = sum(bits_50hz[j+k] << (7-k) for k in range(8))
    byte_data_50hz.append(bval)
print(f"  Bytes: {bytes(byte_data_50hz).hex()}")
for m in re.finditer(b'H7CTF', bytes(byte_data_50hz)):
    print(f"  [FLAG!] {bytes(byte_data_50hz[m.start():m.start()+50])}")

# ============================================================
# Check if the audio itself, when treated as data, decodes to something
# ============================================================
print("\n=== Audio bytes as encoded text ===")
# Read raw PCM from WAV file
wav_file = f'{out_dir}/boardroom.wav'
with open(wav_file, 'rb') as f:
    wav_data = f.read()

# Find data offset
data_offset = wav_data.index(b'data') + 8
raw_pcm = wav_data[data_offset:]

print(f"Raw PCM: {len(raw_pcm)} bytes")

# Try different decodings of raw PCM
# 1. Direct string search
for pattern in [b'H7CTF{', b'flag{', b'FLAG{']:
    if pattern in raw_pcm:
        idx = raw_pcm.index(pattern)
        print(f"  [DIRECT] Found '{pattern}' at offset {idx}")

# 2. XOR with key bytes
for key in [0x55, 0xAA, 0xFF, 0x00, 0x69, 0x42, 0x13, 0x37]:
    xored = bytes(b ^ key for b in raw_pcm[:10000])
    for pattern in [b'H7CTF{', b'flag{', b'FLAG{']:
        if pattern in xored:
            idx = xored.index(pattern)
            print(f"  [XOR key={key:#04x}] Found '{pattern}' at offset {idx}")

# 3. Look at auto_decode tool on some extracted data  
# First, get the spectral features as hex
spectral_str = ''.join(f'{int(v*255):02x}' for v in energy_matrix[2, :])  # 1125Hz channel
print(f"\n1125Hz energy as hex: {spectral_str[:100]}")

# Run auto_decode on the interesting data
import subprocess
test_data = bytes(byte_data_50hz).hex()
print(f"\n50Hz modulation hex: {test_data}")

print("\nDone.")
