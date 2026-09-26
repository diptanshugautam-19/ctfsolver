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
    bs = bytes.fromhex(f)
    print(f"Frame {i}: data={bs[:5].hex()}, sum={sum(bs[:5])}, xor={bs[0]^bs[1]^bs[2]^bs[3]^bs[4]}, last=0x{bs[5]:02x}")
