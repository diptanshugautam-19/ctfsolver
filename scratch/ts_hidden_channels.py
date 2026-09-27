import struct
import re

ts_file = 'solutions/boardroom_av/combined.ts'

with open(ts_file, 'rb') as f:
    ts_data = f.read()

packet_size = 188
num_packets = len(ts_data) // packet_size

print(f"=== MPEG-TS Hidden Channel Analysis ({num_packets} packets) ===\n")

# ============================================================
# 1. PCR (Program Clock Reference) analysis
# PCR is in the adaptation field and encodes a 42-bit clock value
# Hidden bits could be in the PCR extension (9-bit)
# ============================================================
print("--- PCR (Program Clock Reference) Analysis ---")
pcr_values = []
pcr_extensions = []
pcr_packet_indices = []

for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    adaptation = (pkt[3] >> 4) & 3
    
    if adaptation in (2, 3):
        adapt_len = pkt[4]
        if adapt_len >= 6:
            adapt_data = pkt[5:5+adapt_len]
            flags = adapt_data[0]
            has_pcr = (flags >> 4) & 1
            
            if has_pcr:
                # PCR is 6 bytes: 33 bits base + 6 reserved + 9 bits extension
                pcr_bytes = adapt_data[1:7]
                pcr_base = ((pcr_bytes[0] << 25) | (pcr_bytes[1] << 17) | 
                           (pcr_bytes[2] << 9) | (pcr_bytes[3] << 1) | 
                           (pcr_bytes[4] >> 7))
                pcr_ext = ((pcr_bytes[4] & 1) << 8) | pcr_bytes[5]
                pcr = pcr_base * 300 + pcr_ext
                
                pcr_values.append(pcr_base)
                pcr_extensions.append(pcr_ext)
                pcr_packet_indices.append(i)
                
                print(f"  Pkt {i:3d}: PCR_base={pcr_base}, PCR_ext={pcr_ext} ({pcr_ext:#05x})")

print(f"\nTotal PCR packets: {len(pcr_values)}")
if pcr_extensions:
    print(f"PCR ext values: {pcr_extensions}")
    unique_ext = set(pcr_extensions)
    print(f"Unique PCR extensions: {unique_ext}")
    
    # If PCR extensions encode bits (0 or 1 usually vs varied values)
    if max(pcr_extensions) > 1:
        print("PCR extensions have non-binary values - potential data channel!")
        
        # Try to decode as bytes
        ext_bytes = bytearray()
        for j in range(0, len(pcr_extensions)-7, 8):
            bval = sum((1 if pcr_extensions[j+k] else 0) << (7-k) for k in range(8))
            ext_bytes.append(bval)
        print(f"PCR ext bits as bytes: {ext_bytes.hex()}")
        
        # Treat as 9-bit values directly
        ext_data = bytes(pcr_extensions)
        print(f"PCR ext as bytes: {ext_data.hex()}")
        print(f"PCR ext as text: {repr(ext_data)}")

# ============================================================
# 2. PES PTS/DTS analysis
# PTS (Presentation Timestamp) and DTS (Decoding Timestamp) are 33 bits
# ============================================================
print("\n\n--- PES PTS/DTS Analysis ---")
pes_timestamps = []

for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    
    if pid != 0x0100:
        continue
    
    pusi = (pkt[1] >> 6) & 1
    if not pusi:
        continue
    
    adaptation = (pkt[3] >> 4) & 3
    off = 4
    if adaptation in (2, 3):
        off = 5 + pkt[4]
    
    # Check for PES start code
    pes = pkt[off:]
    if pes[:3] != b'\x00\x00\x01':
        continue
    
    stream_id = pes[3]
    pes_len = (pes[4] << 8) | pes[5]
    
    if len(pes) < 9:
        continue
    
    optional_flags1 = pes[6]
    optional_flags2 = pes[7]
    header_len = pes[8]
    
    pts_dts_flags = (optional_flags2 >> 6) & 3
    
    ts_data_local = pes[9:9+header_len]
    
    pts = None
    dts = None
    
    if pts_dts_flags >= 2 and len(ts_data_local) >= 5:
        # PTS: 5 bytes
        pts_bytes = ts_data_local[:5]
        pts = (((pts_bytes[0] & 0x0e) << 29) | 
               ((pts_bytes[1] & 0xff) << 22) | 
               ((pts_bytes[2] & 0xfe) << 14) | 
               ((pts_bytes[3] & 0xff) << 7) | 
               ((pts_bytes[4] & 0xfe) >> 1))
        
        if pts_dts_flags == 3 and len(ts_data_local) >= 10:
            dts_bytes = ts_data_local[5:10]
            dts = (((dts_bytes[0] & 0x0e) << 29) | 
                   ((dts_bytes[1] & 0xff) << 22) | 
                   ((dts_bytes[2] & 0xfe) << 14) | 
                   ((dts_bytes[3] & 0xff) << 7) | 
                   ((dts_bytes[4] & 0xfe) >> 1))
    
    pes_timestamps.append({'pkt': i, 'pts': pts, 'dts': dts, 
                           'flags1': optional_flags1,
                           'raw': ts_data_local[:10].hex()})
    print(f"  Pkt {i:3d}: PTS={pts}, DTS={dts}, flags={optional_flags1:#04x},{optional_flags2:#04x}")
    print(f"    Raw header: {ts_data_local[:10].hex()}")

# Check if PTS/DTS differences encode data
if len(pes_timestamps) > 1:
    pts_list = [t['pts'] for t in pes_timestamps if t['pts'] is not None]
    if len(pts_list) > 1:
        diffs = [pts_list[i+1] - pts_list[i] for i in range(len(pts_list)-1)]
        print(f"\nPTS differences: {diffs}")
        expected_diff = 90000 * 1024 // 48000  # AAC frame at 48kHz = 1024 samples
        print(f"Expected PTS diff for 48kHz/1024 AAC: {expected_diff}")
        deviations = [d - expected_diff for d in diffs]
        print(f"Deviations from expected: {deviations}")
        
        if any(d != 0 for d in deviations):
            print(f"NON-ZERO DEVIATIONS FOUND - potential data channel!")
            dev_bits = [1 if d > 0 else 0 for d in deviations]
            dev_bytes = bytearray()
            for j in range(0, len(dev_bits)-7, 8):
                bval = sum(dev_bits[j+k] << (7-k) for k in range(8))
                dev_bytes.append(bval)
            print(f"Deviations as bytes: {dev_bytes.hex()}")

# ============================================================
# 3. TS Continuity Counter analysis
# Each PID's continuity counter should increment monotonically mod 16
# Unexpected values could encode data
# ============================================================
print("\n\n--- Continuity Counter Analysis ---")
cc_by_pid = {}

for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
    cc = pkt[3] & 0xf
    
    if pid not in cc_by_pid:
        cc_by_pid[pid] = []
    cc_by_pid[pid].append(cc)

for pid, ccs in sorted(cc_by_pid.items()):
    expected = ccs[0]
    errors = []
    for j, cc in enumerate(ccs[1:]):
        expected = (expected + 1) % 16
        if cc != expected:
            errors.append((j+1, cc, expected))
            expected = cc  # resync
    
    print(f"  PID {pid:#06x}: {len(ccs)} packets, {len(errors)} CC errors")
    if errors:
        for pkt_idx, got, expected in errors:
            print(f"    Pkt {pkt_idx}: got {got}, expected {expected} -> delta={got-expected}")

# ============================================================
# 4. Check adaptation field for hidden transport private data
# ============================================================
print("\n\n--- Adaptation Field Private Data Check ---")
for i in range(num_packets):
    pkt = ts_data[i*packet_size:(i+1)*packet_size]
    adaptation = (pkt[3] >> 4) & 3
    
    if adaptation in (2, 3):
        adapt_len = pkt[4]
        if adapt_len > 1:
            adapt_data = pkt[5:5+adapt_len]
            flags = adapt_data[0]
            
            # Check all flags
            has_disc = (flags >> 7) & 1
            has_randinit = (flags >> 6) & 1
            has_esind = (flags >> 5) & 1  # Elementary Stream Priority
            has_pcr = (flags >> 4) & 1
            has_opcr = (flags >> 3) & 1
            has_splicept = (flags >> 2) & 1
            has_tprivdata = (flags >> 1) & 1  # Transport Private Data
            has_afext = flags & 1  # Adaptation Field Extension
            
            if has_tprivdata or has_afext or has_opcr or has_splicept:
                print(f"  Pkt {i}: flags={flags:#04x}: disc={has_disc}, rand={has_randinit}, "
                      f"prio={has_esind}, pcr={has_pcr}, opcr={has_opcr}, "
                      f"splice={has_splicept}, priv={has_tprivdata}, ext={has_afext}")
                print(f"    Adapt data: {adapt_data.hex()}")

print("\n\n=== Done ===")
