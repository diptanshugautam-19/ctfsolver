import subprocess
import os
import struct

segments_dir = 'solutions/boardroom_av/segments'
out_dir = 'solutions/boardroom_av'

# Step 1: Concatenate all TS segments
print("=== Concatenating TS segments ===")
combined = b""
for i in range(6):
    with open(f'{segments_dir}/seg_{i:03d}.ts', 'rb') as f:
        combined += f.read()

combined_ts = f'{out_dir}/combined.ts'
with open(combined_ts, 'wb') as f:
    f.write(combined)
print(f"Combined: {len(combined)} bytes -> {combined_ts}")

# Step 2: Use ffprobe to analyze
print("\n=== ffprobe analysis ===")
try:
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', 
                        combined_ts], capture_output=True, text=True, timeout=10)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr)
except FileNotFoundError:
    print("ffprobe not found, trying ffmpeg")

# Step 3: Extract AAC to WAV using ffmpeg
wav_file = f'{out_dir}/boardroom.wav'
print(f"\n=== Converting to WAV: {wav_file} ===")
try:
    r = subprocess.run(['ffmpeg', '-y', '-i', combined_ts, '-acodec', 'pcm_s16le', 
                        wav_file], capture_output=True, text=True, timeout=30)
    print("STDOUT:", r.stdout)
    print("STDERR:", r.stderr)
    if os.path.exists(wav_file):
        print(f"WAV file created: {os.path.getsize(wav_file)} bytes")
except FileNotFoundError:
    print("ffmpeg not found")

# Step 4: Also extract raw AAC
aac_file = f'{out_dir}/boardroom.aac'
print(f"\n=== Extracting raw AAC: {aac_file} ===")
try:
    r = subprocess.run(['ffmpeg', '-y', '-i', combined_ts, '-acodec', 'copy', 
                        aac_file], capture_output=True, text=True, timeout=30)
    if os.path.exists(aac_file):
        print(f"AAC file created: {os.path.getsize(aac_file)} bytes")
except FileNotFoundError:
    print("ffmpeg not found")

# Step 5: If WAV exists, analyze for steganography
if os.path.exists(wav_file):
    print(f"\n=== Analyzing WAV file ===")
    with open(wav_file, 'rb') as f:
        wav_data = f.read()
    
    # Parse WAV header
    if wav_data[:4] == b'RIFF':
        fmt_offset = wav_data.index(b'fmt ')
        fmt_size = struct.unpack_from('<I', wav_data, fmt_offset + 4)[0]
        audio_fmt, num_channels, sample_rate, byte_rate, block_align, bits_per_sample = \
            struct.unpack_from('<HHIIHH', wav_data, fmt_offset + 8)
        print(f"  Format: {audio_fmt}, Channels: {num_channels}, Sample Rate: {sample_rate}")
        print(f"  Bits/Sample: {bits_per_sample}, Byte Rate: {byte_rate}")
        
        # Find data chunk
        data_offset = wav_data.index(b'data')
        data_size = struct.unpack_from('<I', wav_data, data_offset + 4)[0]
        audio_data = wav_data[data_offset + 8:]
        print(f"  Audio data: {data_size} bytes ({len(audio_data)} available)")
        
        # LSB steganography extraction
        print(f"\n=== LSB Extraction (16-bit samples) ===")
        
        # Extract LSBs from each sample
        if bits_per_sample == 16:
            num_samples = len(audio_data) // 2
            samples = struct.unpack(f'<{num_samples}h', audio_data[:num_samples*2])
            
            # Extract LSB from each sample
            lsb_bits = []
            for s in samples:
                lsb_bits.append(s & 1)
            
            # Convert bits to bytes (MSB first)
            lsb_bytes = bytearray()
            for j in range(0, len(lsb_bits) - 7, 8):
                byte_val = 0
                for k in range(8):
                    byte_val = (byte_val << 1) | lsb_bits[j + k]
                lsb_bytes.append(byte_val)
            
            # Search for flag pattern
            print(f"  LSB bytes: {len(lsb_bytes)} bytes")
            print(f"  First 100 bytes hex: {bytes(lsb_bytes[:100]).hex()}")
            
            # Try to find H7CTF{ in LSB data
            import re
            for m in re.finditer(b'H7CTF\\{', bytes(lsb_bytes)):
                end = bytes(lsb_bytes).index(b'}', m.start()) + 1
                print(f"  [FLAG] {bytes(lsb_bytes[m.start():end]).decode()}")
            
            # Also try printable ASCII
            ascii_out = ""
            for b in lsb_bytes[:500]:
                if 32 <= b < 127:
                    ascii_out += chr(b)
                else:
                    if len(ascii_out) >= 4:
                        print(f"  ASCII run: {ascii_out}")
                    ascii_out = ""
            
            # Try LSB with 2 bits per sample
            print(f"\n=== 2-bit LSB Extraction ===")
            bits_2 = []
            for s in samples:
                bits_2.append((s >> 1) & 1)
                bits_2.append(s & 1)
            
            lsb2_bytes = bytearray()
            for j in range(0, len(bits_2) - 7, 8):
                byte_val = 0
                for k in range(8):
                    byte_val = (byte_val << 1) | bits_2[j + k]
                lsb2_bytes.append(byte_val)
            
            for m in re.finditer(b'H7CTF\\{', bytes(lsb2_bytes)):
                end = bytes(lsb2_bytes).index(b'}', m.start()) + 1
                print(f"  [FLAG-2bit] {bytes(lsb2_bytes[m.start():end]).decode()}")

print("\nDone.")
