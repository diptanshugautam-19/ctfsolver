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

# Let's inspect each frame as bytes:
for i, f in enumerate(frames):
    bs = bytes.fromhex(f)
    print(f"Frame {i}: {[b for b in bs]}")
