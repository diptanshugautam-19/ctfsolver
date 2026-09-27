import wave
import struct
import numpy as np

with wave.open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\reference_ping.wav', 'rb') as w:
    nframes = w.getnframes()
    raw = w.readframes(nframes)

# 24-bit signed PCM
samples = []
for i in range(0, len(raw), 3):
    val = struct.unpack('<i', raw[i:i+3] + (b'\xff' if raw[i+2] & 0x80 else b'\x00'))[0]
    samples.append(val / (1 << 23))

samples = np.array(samples)
print("Samples count:", len(samples))
print("Max amplitude:", np.max(np.abs(samples)))

# FFT
fft_vals = np.abs(np.fft.rfft(samples))
freqs = np.fft.rfftfreq(len(samples), 1.0 / 96000)

top_indices = np.argsort(fft_vals)[-10:][::-1]
print("\nTop Frequencies:")
for idx in top_indices:
    print(f"  {freqs[idx]:8.1f} Hz : magnitude = {fft_vals[idx]:.1f}")
