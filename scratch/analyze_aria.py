import struct
import capstone

with open(r'C:\Users\USER\OneDrive\Desktop\ctf\dog_whistle\aria', 'rb') as f:
    elf = f.read()

# ELF64 header
e_shoff = struct.unpack('<Q', elf[40:48])[0]
e_shentsize = struct.unpack('<H', elf[58:60])[0]
e_shnum = struct.unpack('<H', elf[60:62])[0]
e_shstrndx = struct.unpack('<H', elf[62:64])[0]

sections = []
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack('<IIQQQQIIQQ', elf[off:off+64])
    sections.append({
        'name_idx': sh_name, 'type': sh_type, 'flags': sh_flags, 'addr': sh_addr,
        'offset': sh_offset, 'size': sh_size, 'link': sh_link, 'info': sh_info,
        'entsize': sh_entsize
    })

shstr = elf[sections[e_shstrndx]['offset'] : sections[e_shstrndx]['offset'] + sections[e_shstrndx]['size']]
def get_shstr(idx):
    return shstr[idx:shstr.find(b'\x00', idx)].decode('ascii', errors='ignore')

symtabs = []
for s in sections:
    s['name'] = get_shstr(s['name_idx'])
    print(f"{s['name']:20} type={s['type']:2} addr={hex(s['addr'])} off={hex(s['offset'])} size={hex(s['size'])}")
    if s['type'] in (2, 11): # SHT_SYMTAB, SHT_DYNSYM
        symtabs.append(s)

for symtab in symtabs:
    strtab = sections[symtab['link']]
    str_data = elf[strtab['offset'] : strtab['offset'] + strtab['size']]
    sym_data = elf[symtab['offset'] : symtab['offset'] + symtab['size']]
    entsize = symtab['entsize'] or 24
    num_syms = len(sym_data) // entsize
    print(f"\nSymbols from {symtab['name']} ({num_syms}):")
    for i in range(num_syms):
        st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack('<IBBHQQ', sym_data[i*24:(i+1)*24])
        name = str_data[st_name:str_data.find(b'\x00', st_name)].decode('ascii', errors='ignore')
        if name:
            print(f"  {name:30} val={hex(st_value)} size={st_size} shndx={st_shndx}")
