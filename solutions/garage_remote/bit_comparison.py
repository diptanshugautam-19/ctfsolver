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

bins = [f"{int(f, 16):048b}" for f in frames]

print("Frame index:   " + " ".join(f"{i:2d}" for i in range(8)))
for bit_idx in range(48):
    col = [b[bit_idx] for b in bins]
    is_const = len(set(col)) == 1
    const_marker = f"const {col[0]}" if is_const else "CHANGING: " + "".join(col)
    print(f"Bit {bit_idx:2d}: {const_marker}")
