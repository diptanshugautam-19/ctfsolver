import struct

# Examine the Fill (FIL) elements from AAC frames in detail
# FIL frame 0: de02004c61766336312e31392e313031000240ae5fc543d0d0b4341d0d07
# FIL frame 256: de02004c61766336312e31392e313031000234705ae12ca412850cc97be5

# Let's parse these properly
# AAC FIL element format:
# 3 bits: element ID (110 = 6 = FIL)
# 4 bits: count (if 15, then 8 more bits)
# count * 8 bits: extension payload

fil_hex_0 = 'de02004c61766336312e31392e313031000240ae5fc543d0d0b4341d0d07'
fil_hex_256 = 'de02004c61766336312e31392e313031000234705ae12ca412850cc97be5'

def parse_fil(hex_str, frame_num):
    data = bytes.fromhex(hex_str)
    print(f"\n=== FIL element in frame {frame_num} ===")
    print(f"Raw hex: {hex_str}")
    print(f"Raw bytes: {data}")
    
    # First byte: 0xde = 11011110
    # Bits: 110 11110
    # elem_id = 110 = 6 (FIL) ✓
    # count = 11110 = 30? Wait, count is 4 bits
    # Actually: 0xde = 1101 1110
    # Top 3 bits: 110 = FIL
    # Next 4 bits: 1111 = 15 (means "read next byte for count")
    # Then: 0 (top bit of next nibble)
    
    # Let me do this properly at bit level
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    
    pos = 0
    elem_id = (bits[0] << 2) | (bits[1] << 1) | bits[2]
    pos = 3
    print(f"Element ID: {elem_id} (FIL)")
    
    # count (4 bits)
    count = (bits[pos] << 3) | (bits[pos+1] << 2) | (bits[pos+2] << 1) | bits[pos+3]
    pos += 4
    print(f"Count: {count}")
    
    if count == 15:
        # Read 8 more bits
        esc_count = 0
        for i in range(8):
            esc_count = (esc_count << 1) | bits[pos]
            pos += 1
        count = count + esc_count - 1
        print(f"  Extended count: {esc_count}, total: {count}")
    
    # The fill payload is count bytes (but bit-aligned)
    payload_bits = bits[pos:pos + count*8]
    payload_bytes = bytearray()
    for j in range(0, len(payload_bits) - 7, 8):
        byte_val = 0
        for k in range(8):
            byte_val = (byte_val << 1) | payload_bits[j + k]
        payload_bytes.append(byte_val)
    
    print(f"Payload ({len(payload_bytes)} bytes): {payload_bytes.hex()}")
    print(f"Payload text: {repr(payload_bytes)}")
    
    return payload_bytes

p0 = parse_fil(fil_hex_0, 0)
p256 = parse_fil(fil_hex_256, 256)

# Now let me also look at the full frames more carefully
# Read the raw AAC
aac_file = 'solutions/boardroom_av/boardroom.aac'
with open(aac_file, 'rb') as f:
    aac_data = f.read()

# Parse all ADTS frames and look for any non-SCE/non-FIL elements
print("\n\n=== Full AAC Frame Element Scan ===")
pos = 0
frame_idx = 0
interesting_data = b""

while pos < len(aac_data) - 7:
    if aac_data[pos] == 0xFF and (aac_data[pos+1] & 0xF0) == 0xF0:
        protection = aac_data[pos+1] & 1
        frame_length = ((aac_data[pos+3] & 3) << 11) | (aac_data[pos+4] << 3) | ((aac_data[pos+5] >> 5) & 7)
        header_size = 7 if protection else 9
        
        payload = aac_data[pos+header_size:pos+frame_length]
        
        if len(payload) > 0:
            # Parse element IDs in the frame
            bits = []
            for b in payload:
                for i in range(7, -1, -1):
                    bits.append((b >> i) & 1)
            
            bit_pos = 0
            elements = []
            while bit_pos + 3 <= len(bits):
                eid = (bits[bit_pos] << 2) | (bits[bit_pos+1] << 1) | bits[bit_pos+2]
                elements.append(eid)
                if eid == 7:  # END
                    break
                # We can't easily skip to next element without full parsing
                break  # Just get first element
            
            elem_names = {0: 'SCE', 1: 'CPE', 2: 'CCE', 3: 'LFE', 
                         4: 'DSE', 5: 'PCE', 6: 'FIL', 7: 'END'}
            
            first_elem = elements[0] if elements else -1
            if first_elem not in (0, 7):  # Not SCE or END
                print(f"  Frame {frame_idx}: first_elem={first_elem} ({elem_names.get(first_elem, '?')}), payload[0]={payload[0]:#04x}")
                print(f"    First 30 bytes: {payload[:30].hex()}")
        
        frame_idx += 1
        pos += frame_length
    else:
        pos += 1

# Also look at the actual raw bytes between ADTS frames
print("\n=== Inter-frame gaps ===")
pos = 0
frame_idx = 0
prev_end = 0

while pos < len(aac_data) - 7:
    if aac_data[pos] == 0xFF and (aac_data[pos+1] & 0xF0) == 0xF0:
        if pos > prev_end and frame_idx > 0:
            gap = aac_data[prev_end:pos]
            print(f"  Gap before frame {frame_idx}: {len(gap)} bytes: {gap.hex()}")
        
        frame_length = ((aac_data[pos+3] & 3) << 11) | (aac_data[pos+4] << 3) | ((aac_data[pos+5] >> 5) & 7)
        prev_end = pos + frame_length
        frame_idx += 1
        pos += frame_length
    else:
        pos += 1

# Remaining data after last frame
if prev_end < len(aac_data):
    remaining = aac_data[prev_end:]
    print(f"\nRemaining after last frame: {len(remaining)} bytes: {remaining[:100].hex()}")

print("\nDone.")
