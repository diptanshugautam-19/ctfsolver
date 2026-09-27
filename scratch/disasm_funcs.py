import capstone

with open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\aria', 'rb') as f:
    elf = f.read()

text_addr = 0x1180
text_off = 0x1180
text_size = 0x1829
text = elf[text_off:text_off+text_size]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

def disasm_range(start, end):
    print(f"\n================ Disassembly {hex(start)} to {hex(end)} ================")
    sub_code = elf[start:end]
    for ins in md.disasm(sub_code, start):
        print(f"  {hex(ins.address):8}: {ins.mnemonic:8} {ins.op_str}")

# Let's inspect the function around 0x2600 - 0x29a0 (the command / opcode dispatcher!)
disasm_range(0x2600, 0x29a0)
