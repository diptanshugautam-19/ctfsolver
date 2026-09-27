import struct
import os

# Analyze MPEG-TS segments for hidden data
segments_dir = 'solutions/boardroom_av/segments'

# First, let's concatenate all TS segments and parse the MPEG-TS structure
all_data = b""
for i in range(6):
    with open(f'{segments_dir}/seg_{i:03d}.ts', 'rb') as f:
        all_data += f.read()

print(f"Total TS data: {len(all_data)} bytes")

# Parse MPEG-TS packets (188 bytes each, starting with 0x47)
packet_size = 188
num_packets = len(all_data) // packet_size
print(f"Total packets: {num_packets}")

# Collect PIDs and their types
pids = {}
pat_found = False
pmt_found = False
audio_pids = set()
data_pids = set()

for i in range(num_packets):
    pkt = all_data[i*packet_size:(i+1)*packet_size]
    if pkt[0] != 0x47:
        print(f"  [!] Bad sync byte at packet {i}")
        continue
    
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    if pid not in pids:
        pids[pid] = {'count': 0, 'first_pkt': i}
    pids[pid]['count'] += 1

print("\n=== PID Summary ===")
for pid in sorted(pids.keys()):
    info = pids[pid]
    name = ""
    if pid == 0: name = "(PAT)"
    elif pid == 0x1fff: name = "(Null/Stuffing)"
    elif pid == 0x100: name = "(PMT?)"
    elif pid == 0x101: name = "(Audio?)"
    elif pid < 0x10: name = "(Reserved)"
    print(f"  PID {pid:#06x} ({pid:4d}): {info['count']:4d} packets {name}")

# Parse PAT to find PMT PID
print("\n=== Parsing PAT (PID 0x0000) ===")
for i in range(num_packets):
    pkt = all_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    if pid == 0:
        pusi = (pkt[1] >> 6) & 1
        adaptation = (pkt[3] >> 4) & 3
        payload_offset = 4
        if adaptation in (2, 3):
            adapt_len = pkt[4]
            payload_offset = 5 + adapt_len
        if pusi:
            pointer = pkt[payload_offset]
            payload_offset += 1 + pointer
        
        # PAT table
        if payload_offset < len(pkt):
            table_id = pkt[payload_offset]
            if table_id == 0:  # PAT
                section_length = ((pkt[payload_offset+1] & 0x0f) << 8) | pkt[payload_offset+2]
                # Programs start at offset +8
                prog_offset = payload_offset + 8
                while prog_offset + 4 <= payload_offset + 3 + section_length - 4:
                    prog_num = (pkt[prog_offset] << 8) | pkt[prog_offset+1]
                    pmt_pid = ((pkt[prog_offset+2] & 0x1f) << 8) | pkt[prog_offset+3]
                    print(f"  Program {prog_num} -> PMT PID {pmt_pid:#06x}")
                    prog_offset += 4
        break

# Parse PMT to find stream PIDs
print("\n=== Parsing PMT ===")
for i in range(num_packets):
    pkt = all_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    # Try known PMT PIDs and also any non-zero non-null PID
    if pid not in (0, 0x1fff) and pids[pid]['first_pkt'] == i:
        pusi = (pkt[1] >> 6) & 1
        adaptation = (pkt[3] >> 4) & 3
        payload_offset = 4
        if adaptation in (2, 3):
            adapt_len = pkt[4]
            payload_offset = 5 + adapt_len
        if pusi:
            pointer = pkt[payload_offset]
            payload_offset += 1 + pointer
        
        if payload_offset < len(pkt):
            table_id = pkt[payload_offset]
            if table_id == 2:  # PMT
                section_length = ((pkt[payload_offset+1] & 0x0f) << 8) | pkt[payload_offset+2]
                pcr_pid = ((pkt[payload_offset+8] & 0x1f) << 8) | pkt[payload_offset+9]
                prog_info_len = ((pkt[payload_offset+10] & 0x0f) << 8) | pkt[payload_offset+11]
                print(f"  PMT at PID {pid:#06x}, PCR PID: {pcr_pid:#06x}, prog_info_len: {prog_info_len}")
                
                # Stream entries
                es_offset = payload_offset + 12 + prog_info_len
                while es_offset + 5 <= payload_offset + 3 + section_length - 4:
                    stream_type = pkt[es_offset]
                    es_pid = ((pkt[es_offset+1] & 0x1f) << 8) | pkt[es_offset+2]
                    es_info_len = ((pkt[es_offset+3] & 0x0f) << 8) | pkt[es_offset+4]
                    
                    type_names = {
                        0x03: 'MPEG-1 Audio',
                        0x04: 'MPEG-2 Audio',
                        0x06: 'Private Data',
                        0x0f: 'AAC ADTS',
                        0x11: 'AAC LATM',
                        0x1b: 'H.264/AVC',
                        0x24: 'H.265/HEVC',
                        0x81: 'AC-3',
                        0x87: 'E-AC-3',
                    }
                    tname = type_names.get(stream_type, f'Unknown ({stream_type:#04x})')
                    print(f"  Stream: type={stream_type:#04x} ({tname}), PID={es_pid:#06x}, info_len={es_info_len}")
                    
                    if stream_type == 0x06:
                        data_pids.add(es_pid)
                        print(f"    [!] Private data stream at PID {es_pid:#06x}!")
                        # Show descriptor bytes
                        if es_info_len > 0:
                            desc = pkt[es_offset+5:es_offset+5+es_info_len]
                            print(f"    Descriptors: {desc.hex()}")
                    
                    es_offset += 5 + es_info_len
                break

# Extract payload from all non-PAT, non-PMT, non-null PIDs
print("\n=== Extracting stream payloads ===")
for target_pid in sorted(pids.keys()):
    if target_pid in (0, 0x1fff):
        continue
    
    payload = b""
    for i in range(num_packets):
        pkt = all_data[i*packet_size:(i+1)*packet_size]
        pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
        if pid != target_pid:
            continue
        
        adaptation = (pkt[3] >> 4) & 3
        payload_offset = 4
        if adaptation in (2, 3):
            adapt_len = pkt[4]
            payload_offset = 5 + adapt_len
        if adaptation in (1, 3):  # Has payload
            payload += pkt[payload_offset:]
    
    # Save payload
    outfile = f'{segments_dir}/pid_{target_pid:#06x}.raw'
    with open(outfile, 'wb') as f:
        f.write(payload)
    
    # Check for interesting content
    has_text = False
    for j in range(len(payload) - 4):
        if payload[j:j+4] == b'H7CT' or payload[j:j+4] == b'flag':
            has_text = True
            print(f"  [FLAG?] PID {target_pid:#06x}: found interesting text at offset {j}: {payload[j:j+50]}")
    
    # Check for printable ASCII strings
    ascii_runs = []
    current = b""
    for b in payload:
        if 32 <= b < 127:
            current += bytes([b])
        else:
            if len(current) >= 8:
                ascii_runs.append(current.decode())
            current = b""
    if len(current) >= 8:
        ascii_runs.append(current.decode())
    
    print(f"  PID {target_pid:#06x}: {len(payload)} bytes, {len(ascii_runs)} ASCII strings >=8 chars")
    if target_pid in data_pids:
        print(f"    [DATA PID] - dumping all content")
        print(f"    First 200 bytes hex: {payload[:200].hex()}")
    for s in ascii_runs[:10]:
        print(f"    String: {s}")

print("\n=== Searching entire TS data for flag pattern ===")
import re
for m in re.finditer(b'H7CTF\\{', all_data):
    print(f"  [FLAG] at offset {m.start()}: {all_data[m.start():m.start()+50]}")

# Also check base64/hex encoded flags
for m in re.finditer(b'SDdDVEZ7', all_data):  # base64 of H7CTF{
    print(f"  [BASE64 FLAG] at offset {m.start()}")

for m in re.finditer(b'4837435446', all_data):  # hex of H7CTF
    print(f"  [HEX FLAG] at offset {m.start()}")

print("\nDone.")
