#!/usr/bin/env python3
"""
Convert KDBX 4.x to KDBX 3.1 for better tool compatibility
Requires: pip install pykeepass
"""

from pykeepass import PyKeePass
from pykeepass.kdbx_parsing.kdbx import KDBX4
import sys

def convert_kdbx4_to_31(input_file, output_file, password):
    """Convert KDBX 4.x to KDBX 3.1"""
    
    try:
        print(f"[*] Opening {input_file}...")
        
        # Open KDBX 4 database
        kp = PyKeePass(input_file, password=password)
        
        print(f"[+] Successfully opened database")
        print(f"[*] Database version: {kp.version}")
        
        # Get all entries
        entries = kp.entries
        groups = kp.groups
        
        print(f"[*] Found {len(entries)} entries in {len(groups)} groups")
        
        # Create new KDBX 3.1 database
        print(f"[*] Creating new KDBX 3.1 database: {output_file}")
        
        kp_new = PyKeePass(output_file, password=password, keyfile=None)
        
        # Copy all entries
        root_group = kp_new.root_group
        
        for entry in entries:
            print(f"[*] Copying entry: {entry.title}")
            kp_new.add_entry(
                destination_group=root_group,
                title=entry.title,
                username=entry.username,
                password=entry.password,
                url=entry.url,
                notes=entry.notes
            )
        
        # Save as KDBX 3.1
        kp_new.save()
        
        print(f"\n[+] Conversion complete!")
        print(f"[+] New file: {output_file}")
        print(f"[*] Password: {password}")
        print(f"\n[*] Now you can extract hash with:")
        print(f"    keepass2john {output_file} > hash.txt")
        print(f"    john --wordlist=rockyou.txt hash.txt")
        
        return True
        
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 convert_kdbx.py <input.kdbx> <output.kdbx> <password>")
        print("\nExample:")
        print("  python3 convert_kdbx.py system.kdbx system_v31.kdbx mypassword")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    password = sys.argv[3]
    
    print("[*] KDBX 4 to KDBX 3.1 Converter")
    print("=" * 60)
    
    success = convert_kdbx4_to_31(input_file, output_file, password)
    
    if success:
        print("\n[+] Done!")
    else:
        print("\n[!] Conversion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
