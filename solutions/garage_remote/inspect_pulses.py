import numpy as np

data = np.fromfile('capture.cf32', dtype=np.complex64)
mag = np.abs(data)

# Let's find optimal threshold between high and low
# Plot histogram of mag
hist, bin_edges = np.histogram(mag, bins=50)
print("Mag percentiles:")
for p in [10, 25, 50, 75, 90, 95, 99]:
    print(f"{p}%: {np.percentile(mag, p):.4f}")

thresh = 0.5
high = (mag > thresh).astype(int)

# Run-length encoding of high
diff = np.diff(high)
trans = np.where(diff != 0)[0]

# trans contains indices where transition happened:
# trans[i] to trans[i+1] is a run of either 0 or 1
runs = []
for i in range(len(trans) - 1):
    state = high[trans[i] + 1]
    length = trans[i+1] - trans[i]
    runs.append((state, length, trans[i]))

print(f"Total transitions: {len(trans)}")

# Print first 50 runs
for state, length, idx in runs[:50]:
    print(f"Idx {idx:6d} ({idx/1e6:7.4f}s): State {'HIGH' if state else 'LOW '} for {length:5d} samples ({length/1000:.3f} ms)")
