import av
import numpy as np
from scipy import signal
from scipy.io import wavfile
import struct
import re

out_dir = 'solutions/boardroom_av'
ts_file = f'{out_dir}/combined.ts'

print("=== Decoding audio ===")
container = av.open(ts_file)
all_samples = []
for frame in container.decode(audio=0):
    arr = frame.to_ndarray()
    all_samples.append(arr)
container.close()

audio = np.concatenate(all_samples, axis=-1)[0]  # mono channel
sample_rate = 48000
print(f"Audio: {len(audio)} samples, {len(audio)/sample_rate:.2f}s, range [{audio.min():.4f}, {audio.max():.4f}]")

# 1. Spectrogram analysis - look for hidden messages in frequency domain
print("\n=== Spectrogram Analysis ===")
freqs, times, Sxx = signal.spectrogram(audio, fs=sample_rate, nperseg=1024, noverlap=512)
print(f"Spectrogram: {Sxx.shape} (freq_bins x time_bins)")

# Check for energy at unusual frequencies (hidden tones)
freq_energy = np.mean(Sxx, axis=1)
high_energy_freqs = freqs[freq_energy > np.mean(freq_energy) * 10]
print(f"High-energy frequencies: {high_energy_freqs[:20]}")

# 2. DTMF detection
print("\n=== DTMF Detection ===")
dtmf_freqs = {
    (697, 1209): '1', (697, 1336): '2', (697, 1477): '3', (697, 1633): 'A',
    (770, 1209): '4', (770, 1336): '5', (770, 1477): '6', (770, 1633): 'B',
    (852, 1209): '7', (852, 1336): '8', (852, 1477): '9', (852, 1633): 'C',
    (941, 1209): '*', (941, 1336): '0', (941, 1477): '#', (941, 1633): 'D',
}

# Check for DTMF-like energy  
low_freqs = [697, 770, 852, 941]
high_freqs_dtmf = [1209, 1336, 1477, 1633]

for f in low_freqs + high_freqs_dtmf:
    idx = np.argmin(np.abs(freqs - f))
    energy = np.mean(Sxx[idx])
    if energy > np.mean(freq_energy) * 5:
        print(f"  Significant energy at {freqs[idx]:.0f}Hz (DTMF): {energy:.6f}")

# 3. Check ultrasonic frequencies (above 16kHz) for hidden data
print("\n=== Ultrasonic Analysis (>16kHz) ===")
ultra_mask = freqs > 16000
ultra_energy = np.mean(Sxx[ultra_mask], axis=1)
if np.any(ultra_energy > 0):
    ultra_freqs = freqs[ultra_mask]
    hot = ultra_freqs[ultra_energy > np.mean(ultra_energy) * 5]
    print(f"Hot ultrasonic frequencies: {hot[:10]}")
else:
    print("  No ultrasonic content")

# 4. Try Morse code detection - look for on/off patterns
print("\n=== Amplitude Envelope Analysis ===")
# Calculate amplitude envelope
from scipy.signal import hilbert
analytic = hilbert(audio)
envelope = np.abs(analytic)
# Smooth
window = int(sample_rate * 0.01)  # 10ms window
kernel = np.ones(window) / window
envelope_smooth = np.convolve(envelope, kernel, mode='same')

# Check for clear on/off patterns
threshold = np.mean(envelope_smooth) * 0.5
is_on = envelope_smooth > threshold
transitions = np.diff(is_on.astype(int))
on_starts = np.where(transitions == 1)[0]
off_starts = np.where(transitions == -1)[0]

print(f"  Mean amplitude: {np.mean(envelope_smooth):.6f}")
print(f"  ON segments: {len(on_starts)}, OFF segments: {len(off_starts)}")

# 5. FFT of the entire signal - look for discrete tones
print("\n=== FFT Analysis ===")
fft_vals = np.fft.rfft(audio)
fft_mag = np.abs(fft_vals)
fft_freqs = np.fft.rfftfreq(len(audio), 1/sample_rate)

# Find peaks
peak_indices = signal.find_peaks(fft_mag, height=np.max(fft_mag)*0.01, distance=10)[0]
print(f"Significant FFT peaks ({len(peak_indices)}):")
for idx in peak_indices[:30]:
    print(f"  {fft_freqs[idx]:.1f} Hz: mag={fft_mag[idx]:.2f}")

# 6. Check for data in the raw AAC bitstream (not decoded audio)
print("\n=== Raw AAC Bitstream Analysis ===")
# Read raw AAC from the already extracted file
aac_file = f'{out_dir}/boardroom.aac'
with open(aac_file, 'rb') as f:
    aac_data = f.read()

# Look for patterns that might indicate embedded data
# Check for unusual byte sequences after ADTS headers
pos = 0
frame_payloads = []
while pos < len(aac_data) - 7:
    if aac_data[pos] == 0xFF and (aac_data[pos+1] & 0xF0) == 0xF0:
        protection = aac_data[pos+1] & 1
        frame_length = ((aac_data[pos+3] & 3) << 11) | (aac_data[pos+4] << 3) | ((aac_data[pos+5] >> 5) & 7)
        header_size = 7 if protection else 9
        
        payload = aac_data[pos+header_size:pos+frame_length]
        frame_payloads.append(payload)
        pos += frame_length
    else:
        pos += 1

print(f"Total AAC frames: {len(frame_payloads)}")

# Look for data appended after valid AAC data in each frame
# AAC frames should start with specific element IDs (fill, SCE, CPE, etc.)
for i, payload in enumerate(frame_payloads[:5]):
    if len(payload) > 0:
        # First 3 bits of raw AAC should be element ID
        elem_id = (payload[0] >> 5) & 7
        elem_names = {0: 'SCE', 1: 'CPE', 2: 'CCE', 3: 'LFE', 
                     4: 'DSE', 5: 'PCE', 6: 'FIL', 7: 'END'}
        print(f"  Frame {i}: len={len(payload)}, first_byte={payload[0]:#04x}, elem_id={elem_id} ({elem_names.get(elem_id, '?')})")
        
        # Check for Data Stream Element (DSE, type=4)
        if elem_id == 4:
            print(f"    [!] DATA STREAM ELEMENT found in frame {i}!")
            # DSE can carry arbitrary data
            print(f"    Payload: {payload[:50].hex()}")

# Check ALL frames for DSE
dse_data = b""
for i, payload in enumerate(frame_payloads):
    if len(payload) > 0:
        elem_id = (payload[0] >> 5) & 7
        if elem_id == 4:  # DSE
            dse_data += payload
            print(f"  DSE in frame {i}: {payload[:30].hex()}")

if dse_data:
    print(f"\nTotal DSE data: {len(dse_data)} bytes")
    print(f"DSE hex: {dse_data.hex()}")
else:
    print("\n  No Data Stream Elements found")

# 7. Look for fill elements with embedded data
print("\n=== Fill Element Analysis ===")
for i, payload in enumerate(frame_payloads):
    if len(payload) > 0:
        # Scan through the frame for fill elements (type=6)
        # After the main audio element, there might be fill elements
        elem_id = (payload[0] >> 5) & 7
        if elem_id == 6:  # FIL
            print(f"  FIL in frame {i}: {payload[:30].hex()}")

# 8. Check byte-level entropy differences between frames
print("\n=== Inter-frame Byte Difference Analysis ===")
if len(frame_payloads) > 1:
    # Compare first bytes of consecutive frames
    for i in range(min(5, len(frame_payloads)-1)):
        p1 = frame_payloads[i]
        p2 = frame_payloads[i+1]
        min_len = min(len(p1), len(p2), 20)
        diffs = sum(1 for j in range(min_len) if p1[j] != p2[j])
        print(f"  Frame {i} vs {i+1}: {diffs}/{min_len} bytes differ in first 20")

print("\nDone.")
