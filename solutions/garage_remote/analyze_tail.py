frames = [
    "24ae49095081",
    "24ae49095788",
    "24ae49095e8f",
    "24ae49096587",
    "24ae49096c8e",
    "24ae49097386",
    "24ae49097a8d",
    "24ae49098185",
]

for i, f in enumerate(frames):
    fixed = f[:8]
    tail = f[8:]
    b0 = int(tail[:2], 16)
    b1 = int(tail[2:], 16)
    val16 = int(tail, 16)
    print(f"Frame {i}: tail={tail}, b0=0x{b0:02x} ({b0:3d}), b1=0x{b1:02x} ({b1:3d}), val16={val16} (0x{val16:04x}), bin={b0:08b} {b1:08b}")
