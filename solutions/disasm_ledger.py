import capstone
from ptrlib import ELF

elf = ELF('c:/Users/USER/OneDrive/Desktop/ctf/ledger/ledger')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble from 0x4012b6 (audit) to end of main
with open('c:/Users/USER/OneDrive/Desktop/ctf/ledger/ledger', 'rb') as f:
    raw = f.read()

# Let's find text section
# In ptrlib:
text_sec = elf.section(b'.text')
print(f".text at 0x{text_sec:x}")

# Find offset of .text
# Address 0x401000 or similar
for insn in md.disasm(elf.read(0x4012b6, 0x401700 - 0x4012b6), 0x4012b6):
    print(f"0x{insn.address:x}:\t{insn.mnemonic}\t{insn.op_str}")
