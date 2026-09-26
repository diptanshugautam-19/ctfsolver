from ptrlib import ELF

elf = ELF('c:/Users/USER/OneDrive/Desktop/ctf/ledger/ledger')
got_plt = elf.section(b'.got.plt')
got = elf.section(b'.got')
data = elf.section(b'.data')
bss = elf.section(b'.bss')
print(f".got     at 0x{got:x}")
print(f".got.plt at 0x{got_plt:x}")
print(f".data    at 0x{data:x}")
print(f".bss     at 0x{bss:x}")
