import av
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
import re, struct

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
# High-resolution spectrogram - visualize with text
# ============================================================
print("\n=== Spectrogram text visualization ===")
# The audio has dominant energy at ~1200Hz and ~2160Hz
# Let's see the full picture over time

nperseg = 1024
freqs, times, Sxx = signal.spectrogram(audio, fs=sr, nperseg=nperseg, noverlap=1000,
                                        window='hann')

# Only show frequency bins with any significant energy
Sxx_db = 10 * np.log10(Sxx + 1e-12)
print(f"Spectrogram: {Sxx.shape}, {len(times)} time frames")
print(f"Freq range: 0-{freqs[-1]:.0f}Hz")

# Which frequency bins have above-average energy?
mean_energy = Sxx_db.mean(axis=1)
strong_bins = np.where(mean_energy > np.percentile(mean_energy, 90))[0]
print(f"\nHigh-energy frequency bins ({len(strong_bins)}):")
for b in strong_bins[:20]:
    print(f"  {freqs[b]:.1f}Hz: mean dB={mean_energy[b]:.1f}")

# Show the full spectrogram for those bins over time (as characters)
print("\n--- Time evolution of key frequencies ---")
chars = ' .-:=+*#@'
for bi in strong_bins[:15]:
    row = Sxx_db[bi]
    vmin = row.min()
    vmax = row.max()
    if vmax > vmin:
        norm = (row - vmin) / (vmax - vmin)
    else:
        norm = np.zeros_like(row)
    visual = ''.join(chars[min(int(v * (len(chars)-1)), len(chars)-1)] for v in norm)
    print(f"  {freqs[bi]:7.1f}Hz: {visual}")

# ============================================================
# Check for SSTV (Slow-Scan TV) encoding
# SSTV uses audio frequencies 1200-2300Hz for image transmission
# Robot 36 uses 1200Hz sync, 1500Hz black, 2300Hz white
# ============================================================
print("\n=== SSTV Detection ===")
# SSTV Robot 36: 
# sync pulse: 1200Hz for 5ms
# leader: 1900Hz for 300ms
# separator: 1200Hz for 5ms 
# line data: 1500-2300Hz, 88ms per line

# Look for 1200Hz sync pulses
from scipy.signal import butter, filtfilt, hilbert

def bandpass(data, low, high, fs):
    nyq = fs/2
    b, a = butter(4, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, data)

# 1200Hz sync (SSTV)
sync_filtered = bandpass(audio, 1150, 1250, sr)
sync_env = np.abs(hilbert(sync_filtered))
sync_thresh = sync_env.mean() * 2

# Look for SSTV leader tone at 1900Hz
leader_filtered = bandpass(audio, 1850, 1950, sr)
leader_env = np.abs(hilbert(leader_filtered))

# Look for strong sync pulses
sync_on = sync_env > sync_thresh
sync_changes = np.diff(sync_on.astype(int))
sync_starts = np.where(sync_changes == 1)[0]
sync_ends = np.where(sync_changes == -1)[0]

pulse_lengths = []
for start, end in zip(sync_starts[:50], sync_ends[:50]):
    pulse_ms = (end - start) / sr * 1000
    pulse_lengths.append(pulse_ms)

print(f"1200Hz pulses: {len(sync_starts)} found")
if pulse_lengths:
    print(f"Pulse lengths (ms): {[f'{p:.1f}' for p in pulse_lengths[:20]]}")
    # SSTV sync pulse = 5ms at 1200Hz
    sstv_syncs = [l for l in pulse_lengths if 4 < l < 7]
    print(f"SSTV-compatible pulses (4-7ms): {len(sstv_syncs)}")

# ============================================================
# Instantaneous frequency - FM demodulation
# If the signal uses FSK, we can read the freq directly
# ============================================================
print("\n=== FM/FSK Demodulation ===")
analytic = hilbert(audio)
inst_phase = np.unwrap(np.angle(analytic))
inst_freq = np.diff(inst_phase) * sr / (2 * np.pi)

# Apply LP filter to smooth
nyq = sr/2
b_lp, a_lp = signal.butter(4, 5000/nyq, btype='low')
inst_freq_smooth = signal.filtfilt(b_lp, a_lp, inst_freq)

print(f"Inst freq stats: mean={inst_freq_smooth.mean():.1f}Hz, std={inst_freq_smooth.std():.1f}Hz")

# Quantize to see if we have discrete frequency states
from collections import Counter
freq_quantized = np.round(inst_freq_smooth / 50) * 50  # 50Hz bins
freq_counts = Counter(freq_quantized.tolist())
top_freqs = freq_counts.most_common(20)
print("Top instantaneous frequencies:")
for freq, count in top_freqs:
    pct = 100 * count / len(freq_quantized)
    print(f"  {freq:7.0f}Hz: {count:6d} samples ({pct:.1f}%)")

# ============================================================
# SSTV-specific: if there's a 1900Hz leader followed by varying
# frequencies between 1500Hz (black) and 2300Hz (white), try decoding
# ============================================================
print("\n=== SSTV data extraction ===")
# The audio has energy at ~1200Hz and ~2160Hz (not quite SSTV range, but close)
# Robot36 line frequency range: 1500-2300Hz
# Our audio: 1200Hz and 2160Hz

# Try the assumption that 1200Hz = bit 0 and 2160Hz = bit 1 (FSK)
# Time resolution needed: need to know bit rate

# Detect which frequency is dominant in each 10ms window
window_samples = int(sr * 0.01)
num_windows = len(audio) // window_samples

bits_fsk = []
for i in range(num_windows):
    block = audio[i*window_samples:(i+1)*window_samples]
    
    # Compare energy at 1200Hz vs 2160Hz
    e_1200 = np.abs(rfft(block * signal.windows.hann(len(block))))
    freqs_local = rfftfreq(len(block), 1/sr)
    
    idx_1200 = np.argmin(np.abs(freqs_local - 1200))
    idx_2160 = np.argmin(np.abs(freqs_local - 2160))
    
    e1 = e_1200[idx_1200]
    e2 = e_1200[idx_2160]
    
    if e1 + e2 > 0:
        bits_fsk.append(1 if e2 > e1 else 0)
    else:
        bits_fsk.append(0)

print(f"FSK bits (1200Hz vs 2160Hz, 10ms/bit): {len(bits_fsk)} bits")
print(f"Bits: {bits_fsk[:64]}")

# Decode as bytes
byte_data_fsk = bytearray()
for j in range(0, len(bits_fsk)-7, 8):
    bval = sum(bits_fsk[j+k] << (7-k) for k in range(8))
    byte_data_fsk.append(bval)

print(f"Bytes: {bytes(byte_data_fsk).hex()}")
print(f"First 30 as text: {repr(bytes(byte_data_fsk[:30]))}")

for m in re.finditer(b'H7CTF', bytes(byte_data_fsk)):
    print(f"[FLAG!] {bytes(byte_data_fsk[m.start():m.start()+50])}")

# Try at different bit rates
for bits_per_sec in [100, 50, 200, 150, 300, 75, 25]:
    samples_per_bit = sr // bits_per_sec
    num_bits = len(audio) // samples_per_bit
    
    bits = []
    for i in range(num_bits):
        block = audio[i*samples_per_bit:(i+1)*samples_per_bit]
        spec = np.abs(rfft(block * signal.windows.hann(len(block))))
        freqs_local = rfftfreq(len(block), 1/sr)
        
        idx_1200 = np.argmin(np.abs(freqs_local - 1200))
        idx_2160 = np.argmin(np.abs(freqs_local - 2160))
        
        bits.append(1 if spec[idx_2160] > spec[idx_1200] else 0)
    
    byte_data = bytearray()
    for j in range(0, len(bits)-7, 8):
        bval = sum(bits[j+k] << (7-k) for k in range(8))
        byte_data.append(bval)
    
    for m in re.finditer(b'H7CTF', bytes(byte_data)):
        print(f"[FLAG at {bits_per_sec} bps!] {bytes(byte_data[m.start():m.start()+50])}")
    
    # Check for any printable content
    text = bytes(b for b in byte_data if 32 <= b < 127)
    if len(text) > 10:
        print(f"  {bits_per_sec} bps: readable text = {text[:30]}")

print("\nDone.")
