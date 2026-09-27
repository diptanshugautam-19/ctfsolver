import struct
import re

ts_file = 'solutions/boardroom_av/combined.ts'

with open(ts_file, 'rb') as f:
    ts_data = f.read()

packet_size = 188
num_packets = len(ts_data) // packet_size

print(f"=== MPEG-TS Deep Analysis: {num_packets} packets ===\n")

# 1. Check for data in adaptation fields
print("--- Adaptation Field Analysis ---")
for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    adaptation = (pkt[3] >> 4) & 3
    
    if adaptation in (2, 3):
        adapt_len = pkt[4]
        if adapt_len > 0:
            adapt_data = pkt[5:5+adapt_len]
            flags = adapt_data[0] if adapt_len > 0 else 0
            
            # Check for private data flag (bit 1)
            has_private = (flags >> 1) & 1
            # Check for adaptation field extension
            has_extension = flags & 1
            # Transport private data flag
            has_transport_private = (flags >> 1) & 1
            
            if has_private or has_extension:
                print(f"  Pkt {i}, PID {pid:#06x}: adapt_len={adapt_len}, flags={flags:#04x}, private={has_private}, ext={has_extension}")
                print(f"    Data: {adapt_data.hex()}")
            
            # Look for stuffing bytes that are NOT 0xFF
            if adapt_len > 1:
                # After flags and any optional fields, remaining should be 0xFF stuffing
                # Check if there's non-0xFF data hiding in stuffing
                non_ff = sum(1 for b in adapt_data[1:] if b != 0xff)
                if non_ff > 0 and adapt_len > 6:
                    # There might be actual fields (PCR etc) before stuffing
                    pass

# 2. Extract and analyze raw AAC ADTS frames
print("\n--- AAC ADTS Frame Analysis ---")

# Get PES payload for PID 0x0100
pes_data = b""
for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    if pid != 0x0100:
        continue
    
    pusi = (pkt[1] >> 6) & 1
    adaptation = (pkt[3] >> 4) & 3
    off = 4
    if adaptation in (2, 3):
        off = 5 + pkt[4]
    
    if adaptation in (1, 3):
        pes_data += pkt[off:]

print(f"Raw PES data: {len(pes_data)} bytes")

# Parse PES headers and extract raw AAC
aac_raw = b""
pos = 0
pes_count = 0
while pos < len(pes_data) - 6:
    # Look for PES start code
    if pes_data[pos:pos+3] == b'\x00\x00\x01':
        stream_id = pes_data[pos+3]
        pes_length = (pes_data[pos+4] << 8) | pes_data[pos+5]
        
        if stream_id >= 0xc0 and stream_id <= 0xdf:  # Audio stream
            # Parse PES optional header
            pes_header_len = 0
            if pos + 8 < len(pes_data):
                optional_flags = (pes_data[pos+6] << 8) | pes_data[pos+7]
                pes_header_data_len = pes_data[pos+8]
                payload_start = pos + 9 + pes_header_data_len
                
                if pes_length > 0:
                    payload_end = pos + 6 + pes_length
                else:
                    payload_end = len(pes_data)
                
                payload = pes_data[payload_start:payload_end]
                aac_raw += payload
                pes_count += 1
                
                if pes_count <= 3:
                    print(f"  PES #{pes_count}: stream_id={stream_id:#04x}, pes_len={pes_length}, header_len={pes_header_data_len}")
                    print(f"    Payload start: {payload[:20].hex()}")
        pos += 6 + pes_length if pes_length > 0 else pos + 6
    else:
        pos += 1

print(f"\nTotal PES packets: {pes_count}")
print(f"Total AAC payload: {len(aac_raw)} bytes")

# Save raw AAC with ADTS headers
aac_file = 'solutions/boardroom_av/boardroom.aac'
with open(aac_file, 'wb') as f:
    f.write(aac_raw)
print(f"Saved AAC: {aac_file}")

# Parse ADTS frames
print("\n--- ADTS Frame Parsing ---")
adts_frames = []
pos = 0
while pos < len(aac_raw) - 7:
    # ADTS sync word: 0xFFF
    if aac_raw[pos] == 0xFF and (aac_raw[pos+1] & 0xF0) == 0xF0:
        # Parse ADTS header
        sync = (aac_raw[pos] << 4) | (aac_raw[pos+1] >> 4)
        mpeg_ver = (aac_raw[pos+1] >> 3) & 1  # 0=MPEG-4, 1=MPEG-2
        layer = (aac_raw[pos+1] >> 1) & 3
        protection = aac_raw[pos+1] & 1  # 0=CRC, 1=no CRC
        profile = (aac_raw[pos+2] >> 6) & 3
        sample_freq_idx = (aac_raw[pos+2] >> 2) & 0xf
        private_bit = (aac_raw[pos+2] >> 1) & 1
        channel_cfg = ((aac_raw[pos+2] & 1) << 2) | ((aac_raw[pos+3] >> 6) & 3)
        originality = (aac_raw[pos+3] >> 5) & 1
        home = (aac_raw[pos+3] >> 4) & 1
        copyright_id = (aac_raw[pos+3] >> 3) & 1
        copyright_start = (aac_raw[pos+3] >> 2) & 1
        frame_length = ((aac_raw[pos+3] & 3) << 11) | (aac_raw[pos+4] << 3) | ((aac_raw[pos+5] >> 5) & 7)
        buffer_fullness = ((aac_raw[pos+5] & 0x1f) << 6) | ((aac_raw[pos+6] >> 2) & 0x3f)
        num_aac_frames = (aac_raw[pos+6] & 3) + 1
        
        header_size = 7 if protection else 9  # With CRC it's 9 bytes
        
        adts_frames.append({
            'offset': pos,
            'frame_length': frame_length,
            'private_bit': private_bit,
            'originality': originality,
            'home': home,
            'copyright_id': copyright_id,
            'copyright_start': copyright_start,
            'buffer_fullness': buffer_fullness,
            'profile': profile,
            'sample_freq_idx': sample_freq_idx,
            'channel_cfg': channel_cfg,
        })
        
        pos += frame_length
    else:
        pos += 1

print(f"Total ADTS frames: {len(adts_frames)}")

# Check if private_bit, originality, home, copyright fields carry data
print("\n--- Hidden bits in ADTS header fields ---")
private_bits = [f['private_bit'] for f in adts_frames]
originality_bits = [f['originality'] for f in adts_frames]
home_bits = [f['home'] for f in adts_frames]
copyright_bits = [f['copyright_id'] for f in adts_frames]
copyright_start_bits = [f['copyright_start'] for f in adts_frames]

print(f"  Private bits: {private_bits}")
print(f"  Originality:  {originality_bits}")
print(f"  Home:         {home_bits}")
print(f"  Copyright ID: {copyright_bits}")
print(f"  Copyright St: {copyright_start_bits}")

# Try decoding private bits as bytes
if len(private_bits) >= 8:
    priv_bytes = bytearray()
    for j in range(0, len(private_bits) - 7, 8):
        byte_val = 0
        for k in range(8):
            byte_val = (byte_val << 1) | private_bits[j + k]
        priv_bytes.append(byte_val)
    print(f"  Private bits as bytes: {priv_bytes.hex()} -> {priv_bytes}")

# Combine all single-bit fields
all_bits = []
for f in adts_frames:
    all_bits.extend([f['private_bit'], f['originality'], f['home'], 
                     f['copyright_id'], f['copyright_start']])

combined_bytes = bytearray()
for j in range(0, len(all_bits) - 7, 8):
    byte_val = 0
    for k in range(8):
        byte_val = (byte_val << 1) | all_bits[j + k]
    combined_bytes.append(byte_val)
print(f"  Combined header bits as bytes: {combined_bytes.hex()} -> {combined_bytes}")

# 3. Check for data hiding in TS packet stuffing/padding
print("\n--- TS Packet Content Analysis ---")
# Look at bytes between TS packets (there shouldn't be any)
extra_bytes = len(ts_data) % packet_size
if extra_bytes:
    print(f"  Extra bytes after last packet: {extra_bytes}")
    print(f"  Extra data: {ts_data[-extra_bytes:].hex()}")

# Look for non-standard TS packets
null_packet_content = set()
for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    if pid == 0x1fff:  # Null packets
        null_packet_content.add(pkt[4:].hex()[:40])
        
print(f"  Unique null packet patterns: {len(null_packet_content)}")

# 4. Check for unusual buffer fullness values (could hide data)
print("\n--- Buffer Fullness Values ---")
bf_values = [f['buffer_fullness'] for f in adts_frames]
print(f"  Values: {bf_values}")
# 0x7FF means VBR
unique_bf = set(bf_values)
print(f"  Unique values: {unique_bf}")

# Try treating buffer fullness as data  
if len(set(bf_values)) > 1:
    bf_bytes = bytes([v & 0xFF for v in bf_values])
    print(f"  BF low bytes: {bf_bytes.hex()} -> {bf_bytes}")

# 5. Frame length analysis - look for pattern
print("\n--- Frame Length Pattern ---")
fl_values = [f['frame_length'] for f in adts_frames]
print(f"  Frame lengths: {fl_values}")
# Check if frame length LSBs encode data
fl_lsbs = [v & 1 for v in fl_values]
print(f"  Frame length LSBs: {fl_lsbs}")

print("\nDone.")
