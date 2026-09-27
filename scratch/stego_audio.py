import av
import numpy as np
import struct
import re
import os

out_dir = 'solutions/boardroom_av'
ts_file = f'{out_dir}/combined.ts'

print("=== Decoding audio with PyAV ===")
container = av.open(ts_file)

# Get stream info
for stream in container.streams:
    print(f"  Stream: {stream.type}, codec: {stream.codec_context.name}")
    if stream.type == 'audio':
        print(f"    Sample rate: {stream.codec_context.sample_rate}")
        print(f"    Channels: {stream.codec_context.channels}")
        print(f"    Format: {stream.codec_context.format}")

# Decode all audio frames
container.seek(0)
all_samples = []
for frame in container.decode(audio=0):
    # Convert to numpy
    arr = frame.to_ndarray()
    all_samples.append(arr)
    
container.close()

# Concatenate all samples
audio = np.concatenate(all_samples, axis=-1)
print(f"\nAudio shape: {audio.shape}, dtype: {audio.dtype}")
print(f"Sample range: [{audio.min()}, {audio.max()}]")
print(f"Total samples: {audio.shape[-1]}")

# If float format, convert to 16-bit integers
if audio.dtype in (np.float32, np.float64):
    # Float audio is typically -1.0 to 1.0
    # For AAC it's typically in fltp format (float planar)
    print(f"Float audio - range [{audio.min():.6f}, {audio.max():.6f}]")
    audio_int = (audio * 32767).astype(np.int16)
else:
    audio_int = audio

# Save as raw PCM
pcm_file = f'{out_dir}/boardroom.pcm'
audio_int.tofile(pcm_file)
print(f"Saved PCM: {os.path.getsize(pcm_file)} bytes")

# Also save as WAV manually
wav_file = f'{out_dir}/boardroom.wav'
if len(audio_int.shape) == 1:
    num_channels = 1
    samples_flat = audio_int
else:
    num_channels = audio_int.shape[0]
    # Interleave channels
    samples_flat = audio_int.T.flatten()

sample_rate = 48000  # Will confirm from stream
with open(wav_file, 'wb') as f:
    num_samples = len(samples_flat)
    data_size = num_samples * 2
    f.write(b'RIFF')
    f.write(struct.pack('<I', 36 + data_size))
    f.write(b'WAVE')
    f.write(b'fmt ')
    f.write(struct.pack('<IHHIIHH', 16, 1, num_channels, sample_rate,
                        sample_rate * num_channels * 2, num_channels * 2, 16))
    f.write(b'data')
    f.write(struct.pack('<I', data_size))
    f.write(samples_flat.tobytes())
print(f"Saved WAV: {os.path.getsize(wav_file)} bytes")

# === STEGANOGRAPHY ANALYSIS ===
# Work with the first channel if stereo
if len(audio_int.shape) > 1:
    ch0 = audio_int[0]
    ch1 = audio_int[1] if audio_int.shape[0] > 1 else None
else:
    ch0 = audio_int
    ch1 = None

print(f"\n=== Channel 0: {len(ch0)} samples ===")

# 1. LSB extraction
print("\n--- LSB Extraction (1-bit per sample, MSB-first bytes) ---")
lsb_bits = [int(s) & 1 for s in ch0]
lsb_bytes = bytearray()
for j in range(0, len(lsb_bits) - 7, 8):
    byte_val = 0
    for k in range(8):
        byte_val = (byte_val << 1) | lsb_bits[j + k]
    lsb_bytes.append(byte_val)

lsb_data = bytes(lsb_bytes)
print(f"  Extracted {len(lsb_data)} bytes")
print(f"  First 100 hex: {lsb_data[:100].hex()}")

# Check for flag
for m in re.finditer(b'H7CTF\\{', lsb_data):
    end_idx = lsb_data.index(b'}', m.start()) + 1
    print(f"  [FLAG!] {lsb_data[m.start():end_idx].decode()}")

# Check for printable text
printable = ""
for b in lsb_data[:2000]:
    if 32 <= b < 127:
        printable += chr(b)
    else:
        if len(printable) >= 6:
            print(f"  ASCII: {printable}")
        printable = ""

# 2. LSB extraction (LSB-first bit order)
print("\n--- LSB Extraction (1-bit per sample, LSB-first bytes) ---")
lsb_bytes2 = bytearray()
for j in range(0, len(lsb_bits) - 7, 8):
    byte_val = 0
    for k in range(8):
        byte_val |= (lsb_bits[j + k] << k)
    lsb_bytes2.append(byte_val)

lsb_data2 = bytes(lsb_bytes2)
print(f"  First 100 hex: {lsb_data2[:100].hex()}")
for m in re.finditer(b'H7CTF\\{', lsb_data2):
    end_idx = lsb_data2.index(b'}', m.start()) + 1
    print(f"  [FLAG!] {lsb_data2[m.start():end_idx].decode()}")

# 3. If stereo, check channel difference for hidden data
if ch1 is not None:
    print("\n--- Channel Difference Analysis ---")
    diff = ch0.astype(np.int32) - ch1.astype(np.int32)
    nonzero = np.count_nonzero(diff)
    print(f"  Non-zero differences: {nonzero}/{len(diff)}")
    
    if nonzero > 0:
        # The difference could contain hidden data
        diff_abs = np.abs(diff)
        print(f"  Max diff: {diff_abs.max()}, Mean diff: {diff_abs[diff_abs > 0].mean():.2f}")
        
        # Try extracting bits from difference
        diff_bits = [1 if d != 0 else 0 for d in diff]
        diff_bytes = bytearray()
        for j in range(0, len(diff_bits) - 7, 8):
            byte_val = 0
            for k in range(8):
                byte_val = (byte_val << 1) | diff_bits[j + k]
            diff_bytes.append(byte_val)
        
        diff_data = bytes(diff_bytes)
        print(f"  Diff bytes: {diff_data[:100].hex()}")
        for m in re.finditer(b'H7CTF\\{', diff_data):
            end_idx = diff_data.index(b'}', m.start()) + 1
            print(f"  [FLAG!] {diff_data[m.start():end_idx].decode()}")
        
        # Try treating the difference values themselves as data
        diff_nonzero = diff[diff != 0]
        print(f"  Non-zero diff values (first 50): {diff_nonzero[:50].tolist()}")
        
        # Maybe the diff values encode bytes directly
        if max(abs(d) for d in diff_nonzero[:100]) <= 255:
            msg = bytes([abs(int(d)) for d in diff_nonzero[:100]])
            print(f"  Diff as bytes: {msg[:50]}")
            print(f"  Diff as bytes hex: {msg[:50].hex()}")

# 4. Check if there are any unusual patterns in sample values
print("\n--- Sample Value Analysis ---")
unique = np.unique(ch0)
print(f"  Unique values: {len(unique)}")
print(f"  Sample histogram (LSB=0 vs LSB=1):")
lsb0 = np.sum(ch0 & 1 == 0)
lsb1 = np.sum(ch0 & 1 == 1)
print(f"    LSB=0: {lsb0}, LSB=1: {lsb1}, ratio: {lsb1/lsb0:.4f}")

# 5. Search for patterns in raw bytes of audio data
print("\n--- Raw byte search in audio data ---")
raw_bytes = audio_int.tobytes()
for pattern in [b'H7CTF{', b'flag{', b'FLAG{', b'h7ctf{', b'SDdDVEZ7', b'4837435446']:
    idx = raw_bytes.find(pattern)
    if idx >= 0:
        print(f"  Found '{pattern}' at byte offset {idx}: {raw_bytes[idx:idx+50]}")

# 6. Check MPEG-TS ancillary data / ID3 tags
print("\n--- Checking TS for ID3/metadata tags ---")
with open(ts_file, 'rb') as f:
    ts_data = f.read()

for tag in [b'ID3', b'PRIV', b'TXXX', b'COMM', b'APIC', b'GEOB']:
    idx = ts_data.find(tag)
    if idx >= 0:
        print(f"  Found {tag} at offset {idx}: {ts_data[idx:idx+100].hex()}")

# Look for any extra PES private data
for i in range(0, len(ts_data) - 188, 188):
    pkt = ts_data[i:i+188]
    if pkt[0] != 0x47:
        continue
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    if pid == 0x0011:  # SDT
        # Extract payload
        adaptation = (pkt[3] >> 4) & 3
        off = 4
        if adaptation in (2, 3):
            off = 5 + pkt[4]
        payload = pkt[off:]
        # Look for any text
        text_parts = re.findall(rb'[\x20-\x7e]{4,}', payload)
        if text_parts:
            for t in text_parts:
                print(f"  SDT text: {t.decode()}")

print("\nDone.")
