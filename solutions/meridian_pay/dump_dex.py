import struct
import os

dex_path = "solutions/meridian_pay/extracted/classes.dex"
with open(dex_path, "rb") as f:
    dex = f.read()

assert dex[:4] == b"dex\n", "Not a DEX file"

# DEX header
# string_ids_size at 0x38, string_ids_off at 0x3C
string_ids_size, string_ids_off = struct.unpack_from("<II", dex, 0x38)
print(f"string_ids_size: {string_ids_size}, string_ids_off: 0x{string_ids_off:x}")

strings = []
for i in range(string_ids_size):
    str_data_off = struct.unpack_from("<I", dex, string_ids_off + i * 4)[0]
    # LEB128 length followed by MUTF-8 string
    pos = str_data_off
    # read uleb128
    length = 0
    shift = 0
    while True:
        b = dex[pos]
        pos += 1
        length |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    # read until null byte
    end = dex.find(b"\x00", pos)
    s = dex[pos:end].decode("utf-8", errors="replace")
    strings.append(s)

print(f"\n[+] Extracted {len(strings)} strings from classes.dex:")
for s in strings:
    if len(s) > 2 and not s.startswith("Ljava/") and not s.startswith("Landroid/"):
        print(f"  {s}")

print("\n[*] Searching for H7CTF flags or endpoints or tokens in strings...")
for s in strings:
    if "H7CTF" in s or "flag" in s.lower() or "token" in s.lower() or "secret" in s.lower() or "api" in s.lower() or "http" in s.lower():
        print("  -->", s)
