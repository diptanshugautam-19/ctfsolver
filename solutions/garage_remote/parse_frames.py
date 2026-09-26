import numpy as np

data = np.fromfile('capture.cf32', dtype=np.complex64)
mag = np.abs(data)
thresh = 0.5
high = (mag > thresh).astype(int)

diff = np.diff(high)
trans = np.where(diff != 0)[0]

runs = []
for i in range(len(trans) - 1):
    state = high[trans[i] + 1]
    length = trans[i+1] - trans[i]
    runs.append((state, length, trans[i]))

# Look for long LOWs
print("Gaps / Long LOW periods:")
for state, length, idx in runs:
    if state == 0 and length > 1500:
        print(f"Gap at idx {idx} ({idx/1e6:.4f}s): LOW for {length} samples ({length/1000:.2f} ms)")

# Group into frames
frames = []
curr_frame = []
for i in range(0, len(runs)):
    state, length, idx = runs[i]
    if state == 1:
        # Check next run for low duration
        low_len = runs[i+1][1] if i+1 < len(runs) else 0
        curr_frame.append((length, low_len))
        if low_len > 1500:
            frames.append(curr_frame)
            curr_frame = []

if curr_frame:
    frames.append(curr_frame)

print(f"\nTotal frames detected: {len(frames)}")
for i, f in enumerate(frames):
    print(f"Frame {i}: {len(f)} symbols")
