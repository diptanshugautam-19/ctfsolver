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

# Let's inspect nibbles of all frames:
for i, f in enumerate(frames):
    nibbles = [int(c, 16) for c in f]
    print(f"Frame {i}: nibbles={nibbles}, sum_all={sum(nibbles)}, sum_first10={sum(nibbles[:10])}, sum_first11={sum(nibbles[:11])}")

print("\nCheck sum(nibbles[:10]) mod various numbers:")
for m in range(2, 32):
    res = [sum([int(c, 16) for c in f][:10]) % m for f in frames]
    last_nib = [int(f[-1], 16) for f in frames]
    if len(set(res)) > 1: # not constant
        # check if linear match
        print(f"mod {m:2d}: {res} vs last_nib {last_nib}")
