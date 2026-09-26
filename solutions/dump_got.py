from ptrlib import ELF

elf = ELF('c:/Users/USER/OneDrive/Desktop/ctf/ledger/ledger')
funcs = ['free', 'puts', 'write', 'fclose', 'printf', 'read', 'fgets', 'malloc', 'setvbuf', 'fopen', 'atoi', 'exit']
for f in funcs:
    try:
        addr = elf.got(f)
        plt_addr = elf.plt(f)
        print(f"{f:10s} : GOT = 0x{addr:x}, PLT = 0x{plt_addr:x}")
    except Exception as e:
        print(f"{f:10s} : {e}")
