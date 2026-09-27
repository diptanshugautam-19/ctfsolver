import struct

with open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\aria', 'rb') as f:
    elf = f.read()

# Let's inspect the RIP-relative offsets from 0x1f86, 0x1f8e, 0x1f9c, 0x1fa4:
# 0x1f86: rip + 0x1362 -> 0x1f8e + 0x1362 = 0x32f0
# 0x1f8e: rip + 0x1362 -> 0x1f96 + 0x1362 = 0x32f8
# 0x1f9c: rip + 0x135c -> 0x1fa4 + 0x135c = 0x3300
# 0x1fa4: rip + 0x135c -> 0x1fac + 0x135c = 0x3308

for addr in [0x32e0, 0x32e8, 0x32f0, 0x32f8, 0x3300, 0x3308, 0x3310, 0x3318]:
    val_double = struct.unpack('<d', elf[addr:addr+8])[0]
    val_float = struct.unpack('<ff', elf[addr:addr+8])
    print(f"{hex(addr)}: double={val_double}  floats={val_float}")
