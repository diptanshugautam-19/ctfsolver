import socket
import ssl
import re

ts_file = 'solutions/boardroom_av/combined.ts'
with open(ts_file, 'rb') as f:
    ts_data = f.read()

# Search for 'NTEFL}' context
print("=== Searching for flag fragments in TS data ===")
# Look for 'NTEFL}' with context
for i in range(len(ts_data)):
    if ts_data[i:i+6] == b'NTEFL}':
        start = max(0, i-30)
        print(f"NTEFL}} at {i}: ...{ts_data[start:i+10].hex()}...")
        printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ts_data[start:i+10])
        print(f"  Text: {printable}")

# Look for H7CTF or variations with any encoding
print("\n=== Searching for flag variations ===")
patterns = [
    b'H7CTF{', b'h7ctf{', b'H7CTF', b'7CTF{',
    b'flag{', b'FLAG{', b'Flag{',
    b'\x48\x37\x43\x54\x46\x7b',  # H7CTF{
]
for pat in patterns:
    idx = 0
    while True:
        idx = ts_data.find(pat, idx)
        if idx < 0:
            break
        print(f"Found {pat} at offset {idx}: {ts_data[idx:idx+60].hex()}")
        printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ts_data[idx:idx+60])
        print(f"  Text: {printable}")
        idx += 1

# Also try auto_decode on selected data
print("\n=== Running auto_decode on various extracts ===")
import subprocess

# Extract the audio PES payload (skipping PES headers)
# Focus on bytes around the FIL element at frame 0
with open('solutions/boardroom_av/boardroom.aac', 'rb') as f:
    aac_data = f.read()

# Get the first 200 bytes of AAC data
test_data = aac_data[:200].hex()
r = subprocess.run(['python', 'tools/auto_decode.py', test_data], 
                  capture_output=True, text=True, timeout=30,
                  cwd='c:\\Users\\USER\\OneDrive\\Desktop\\ctf')
print(f"auto_decode result: {r.stdout[:500]}")

# Also try the string 'NTEFL}' backwards  
print("\n=== Trying NTEFL} reversed: }LFTEN ===")
print("Reversed NTEFL} = }LFTEN")
print("Not matching known flag format")

# Look for the string in different encodings 
print("\n=== Looking for 'H7CTF' XOR'd with various keys ===")
target = b'H7CTF{'
for key in range(256):
    xor_target = bytes(b ^ key for b in target)
    if xor_target in ts_data:
        idx = ts_data.index(xor_target)
        print(f"  XOR {key}: found at offset {idx}")
        # Decode more bytes
        extracted = bytes(b ^ key for b in ts_data[idx:idx+50])
        print(f"  Decoded: {extracted}")

# Check if any segment of the audio bytes XOR'd equals flag content
print("\n=== Checking audio WAV for XOR-encoded flag ===")
with open('solutions/boardroom_av/boardroom.wav', 'rb') as f:
    wav_data = f.read()

for key in range(256):
    xored = bytes(b ^ key for b in wav_data[44:44+10000])  # Skip header
    if b'H7CTF{' in xored:
        idx = xored.index(b'H7CTF{')
        print(f"  WAV XOR {key}: flag at {idx+44}")
        print(f"  {xored[idx:idx+50]}")

print("\nDone.")
