import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, filtfilt, hilbert

sr, data = wavfile.read('solutions/boardroom_av/boardroom.wav')
burst = data[97025:177344].astype(float)
burst = burst / np.max(np.abs(burst))

# Bandpass filter around 1000 - 2400 Hz to remove noise and 50Hz hum
b_bp, a_bp = butter(4, [1000 / (sr/2), 2400 / (sr/2)], btype='band')
filtered = filtfilt(b_bp, a_bp, burst)

# Method 1: Analytic signal (Hilbert transform) to get instantaneous frequency
analytic = hilbert(filtered)
inst_phase = np.unwrap(np.angle(analytic))
inst_freq = np.diff(inst_phase) * sr / (2 * np.pi)

# Low pass filter instantaneous frequency with cutoff at 1200 Hz
b_lp, a_lp = butter(4, 1200 / (sr/2), btype='low')
smooth_freq = filtfilt(b_lp, a_lp, inst_freq)

# Midpoint between 1200 and 2200 is 1700 Hz
freq_deviation = smooth_freq - 1700.0

print(f"Smooth freq range: min={smooth_freq.min():.1f}, max={smooth_freq.max():.1f}, mean={smooth_freq.mean():.1f}")

# Let's inspect the frequency over the first 500 samples (at 40 samples per bit)
# 40 samples = 1 bit
baud = 1200.0
spb = sr / baud

# Let's find clock recovery using a simple digital PLL or Gardner / Mueller & Müller
# Or simply test offsets 0..39:
for offset in range(40):
    sample_indices = np.arange(offset, len(freq_deviation), int(spb))
    bits = (freq_deviation[sample_indices] < 0).astype(int) # True if < 1700 Hz (Mark = 1200 Hz)
    
    # 1 = Mark (<1700), 0 = Space (>1700)
    # Test NRZI:
    nrzi = [1 if bits[i] == bits[i-1] else 0 for i in range(1, len(bits))]
    nrzi_str = "".join(map(str, nrzi))
    
    # Also test inverted NRZI: 0 if bits[i] == bits[i-1] else 1
    nrzi_inv = [0 if bits[i] == bits[i-1] else 1 for i in range(1, len(bits))]
    nrzi_inv_str = "".join(map(str, nrzi_inv))
    
    c1 = nrzi_str.count("01111110")
    c2 = nrzi_inv_str.count("01111110")
    
    if c1 > 0 or c2 > 0:
        print(f"Offset {offset:2d}: count(01111110) in nrzi = {c1}, in inv = {c2}")

