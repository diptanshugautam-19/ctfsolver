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

frames = []
curr_frame = []
for i in range(len(runs)):
    state, length, idx = runs[i]
    if state == 1:
        low_len = runs[i+1][1] if i+1 < len(runs) else 0
        curr_frame.append((length, low_len))
        if low_len > 1500:
            frames.append(curr_frame)
            curr_frame = []
if curr_frame:
    frames.append(curr_frame)

for f_idx, frame in enumerate(frames):
    print(f"--- Frame {f_idx} (len {len(frame)}) ---")
    high_lens = [p[0] for p in frame]
    low_lens = [p[1] for p in frame]
    print("High lengths:", high_lens)
    print("Low lengths:", low_lens)
