import numpy as np

# Load capture
data = np.fromfile('capture.cf32', dtype=np.complex64)
print(f"Total samples: {len(data)}, duration: {len(data)/1e6:.4f} s")

# Envelope
mag = np.abs(data)
print(f"Min mag: {mag.min():.4f}, Max mag: {mag.max():.4f}, Mean mag: {mag.mean():.4f}, Median mag: {np.median(mag):.4f}")

# Threshold to find active regions
thresh = (mag.max() + np.median(mag)) / 4
print(f"Threshold: {thresh:.4f}")

active = mag > thresh
# Find transitions
diff = np.diff(active.astype(int))
starts = np.where(diff == 1)[0]
ends = np.where(diff == -1)[0]

print(f"Starts count: {len(starts)}, Ends count: {len(ends)}")

# Let's inspect power smoothed or aggregated over chunks
window = 500  # 0.5 ms
smoothed = np.convolve(mag, np.ones(window)/window, mode='same')

# Find bursts separated by silence (say > 5 ms = 5000 samples)
burst_active = smoothed > thresh / 2
diff_burst = np.diff(burst_active.astype(int))
b_starts = np.where(diff_burst == 1)[0]
b_ends = np.where(diff_burst == -1)[0]

print(f"Rough bursts: {len(b_starts)}")
if len(b_starts) > 0 and len(b_ends) > 0:
    for i in range(min(15, len(b_starts))):
        end_val = b_ends[i] if i < len(b_ends) else len(data)
        dur_ms = (end_val - b_starts[i]) / 1000
        print(f"Burst {i}: start={b_starts[i]} ({b_starts[i]/1e6:.4f}s), dur={dur_ms:.2f}ms")
