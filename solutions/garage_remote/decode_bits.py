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

print(f"Num frames: {len(frames)}")

# For each frame, examine all 49 symbols
for i, f in enumerate(frames):
    highs = [round(p[0] / 300) for p in f] # 300 -> 1, 600 -> 2
    print(f"Frame {i}: {highs}")

# Check 48-bit interpretations:
# Case A: pulses 0..47 are bits, pulse 48 is stop bit (or trailing pulse)
#   Hypothesis A1: 300 -> 0, 600 -> 1
#   Hypothesis A2: 300 -> 1, 600 -> 0
# Case B: pulse 0 is start bit, pulses 1..48 are bits
#   Hypothesis B1: 300 -> 0, 600 -> 1
#   Hypothesis B2: 300 -> 1, 600 -> 0

for case_name, start_idx, end_idx in [("pulses 0..47 (last is stop)", 0, 48), ("pulses 1..48 (first is start)", 1, 49)]:
    print(f"\n=== Testing {case_name} ===")
    for invert in [False, True]:
        label = "300=1, 600=0" if invert else "300=0, 600=1"
        print(f"\n--- {label} ---")
        hex_codes = []
        for i, f in enumerate(frames):
            bits = []
            for p in f[start_idx:end_idx]:
                val = 1 if p[0] > 450 else 0
                if invert:
                    val = 1 - val
                bits.append(val)
            bitstr = "".join(str(b) for b in bits)
            val_int = int(bitstr, 2)
            hex_str = f"{val_int:012x}"
            hex_codes.append(hex_str)
            print(f"Frame {i}: {hex_str} (bin: {bitstr})")
