from ptrlib import ELF

elf = ELF('c:/Users/USER/OneDrive/Desktop/ctf/ledger/ledger')
rodata = elf.section(b'.rodata')
print(f".rodata at 0x{rodata:x}")
content = elf.read(rodata, 0x1000)

pos = 0
while pos < len(content):
    end = content.find(b'\x00', pos)
    if end == -1:
        break
    s = content[pos:end]
    if len(s) > 1 and all(32 <= b <= 126 or b in [10, 13, 9] for b in s):
        print(f"0x{rodata + pos:x}: {s}")
    pos = end + 1
