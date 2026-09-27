import struct
import capstone

with open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\aria', 'rb') as f:
    elf = f.read()

# Let's find addresses of key strings in .rodata
rodata_addr = 0x3000
rodata_off = 0x3000
rodata = elf[rodata_off:rodata_off+0x3d0]

targets = [
    b"SAFETY LOCKOUT",
    b"FACTORY DIAG UNLOCKED",
    b"FLAG: %s",
    b"PROFILE SELECTED",
    b"CAL ECHO",
    b"CAL VECTOR WRITTEN",
    b"PONG",
    b"eq.cfg",
]

str_addrs = {}
for t in targets:
    idx = rodata.find(t)
    if idx != -1:
        str_addrs[t.decode()] = rodata_addr + idx
        print(f"{t.decode():25}: {hex(rodata_addr + idx)}")

# Now disassemble .text and find RIP-relative references to these strings
text_addr = 0x1180
text_off = 0x1180
text_size = 0x1829
text = elf[text_off:text_off+text_size]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True

print("\n--- Cross References ---")
for ins in md.disasm(text, text_addr):
    # Check RIP relative lea / mov
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
            target = ins.address + ins.size + op.mem.disp
            for sname, saddr in str_addrs.items():
                if target == saddr:
                    print(f"{hex(ins.address)}: {ins.mnemonic} {ins.op_str}  --> [{sname}]")
