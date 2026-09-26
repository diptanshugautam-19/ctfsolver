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

def rev_byte(b):
    return int(f"{b:08b}"[::-1], 2)

print("--- Whole frame bit reverse ---")
for i, f in enumerate(frames):
    bits = f"{int(f, 16):048b}"
    rev_bits = bits[::-1]
    rev_hex = f"{int(rev_bits, 2):012x}"
    print(f"Frame {i}: {rev_hex}")

print("\n--- Byte-by-byte bit reverse ---")
for i, f in enumerate(frames):
    bs = bytes.fromhex(f)
    rev_bs = bytes([rev_byte(b) for b in bs])
    print(f"Frame {i}: {rev_bs.hex()}")
