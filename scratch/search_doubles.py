import struct

with open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\aria', 'rb') as f:
    elf = f.read()

rodata = elf[0x3000:0x33d0]
for i in range(0, len(rodata)-8, 8):
    d = struct.unpack('<d', rodata[i:i+8])[0]
    if 10.0 < abs(d) < 100000.0:
        print(f"Offset {hex(0x3000+i)}: {d}")
