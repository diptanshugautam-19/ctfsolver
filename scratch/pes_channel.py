"""
PES-batching covert channel decoder.

Observation: In the 5.7s VOD capture, PTS diffs between consecutive PES
headers were either 15360 (8 × 1920) or 13440 (7 × 1920), where 1920
is the expected PTS increment for one AAC frame (1024 samples @ 48kHz,
scaled by 90000/48000). Fewer frames per PES packet vs more = bit 0 vs 1
(or vice versa). We need more data to resolve the message.

This script:
  1. Scans a directory of .ts segments in order.
  2. Extracts PES headers from audio PID.
  3. Computes frame_count = round(pts_diff / 1920) per PES.
  4. Drops segment-boundary transitions (anomalous values).
  5. Maps frame counts to bits: 7 frames -> 0, 8 frames -> 1.
  6. Brute-forces alignment (offset 0-7) and polarity to find H7CTF{.
"""

import os
import re
import glob
import struct
import sys

AUDIO_PID = 0x0100
FRAME_UNIT = 1920   # 1024 samples @ 48 kHz × (90000/48000)
PACKET_SIZE = 188

def parse_pts(pes_header_bytes):
    """Parse PTS from 5-byte PTS field (after optional header)."""
    if len(pes_header_bytes) < 5:
        return None
    b = pes_header_bytes
    pts = (((b[0] & 0x0e) << 29) |
           ((b[1] & 0xff) << 22) |
           ((b[2] & 0xfe) << 14) |
           ((b[3] & 0xff) << 7) |
           ((b[4] & 0xfe) >> 1))
    return pts

def extract_pts_from_segment(ts_bytes):
    """Return list of (pkt_index, pts) for every PES start in audio PID."""
    pts_list = []
    n = len(ts_bytes) // PACKET_SIZE
    for i in range(n):
        pkt = ts_bytes[i * PACKET_SIZE:(i + 1) * PACKET_SIZE]
        if pkt[0] != 0x47:
            continue
        pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
        if pid != AUDIO_PID:
            continue
        pusi = (pkt[1] >> 6) & 1
        if not pusi:
            continue
        adaptation = (pkt[3] >> 4) & 3
        off = 4
        if adaptation in (2, 3):
            off = 5 + pkt[4]
        pes = pkt[off:]
        if len(pes) < 14 or pes[:3] != b'\x00\x00\x01':
            continue
        pts_dts_flags = (pes[7] >> 6) & 3
        header_data_len = pes[8]
        if pts_dts_flags >= 2 and len(pes) >= 14:
            pts = parse_pts(pes[9:14])
            if pts is not None:
                pts_list.append((i, pts))
    return pts_list

def pts_to_bits(pts_list, frame_unit=FRAME_UNIT, boundary_tolerance=0.15):
    """
    Convert consecutive PTS differences to frame counts, then to bits.
    frame_count = round(pts_diff / frame_unit)
    Drops values that aren't close to an integer multiple (boundary artifact guard).
    Returns list of (frame_count, pts_diff) and the raw bits.
    """
    frame_counts = []
    for j in range(len(pts_list) - 1):
        _, pts_a = pts_list[j]
        _, pts_b = pts_list[j + 1]
        diff = pts_b - pts_a
        if diff <= 0:
            continue
        ratio = diff / frame_unit
        nearest_int = round(ratio)
        if abs(ratio - nearest_int) < boundary_tolerance and nearest_int > 0:
            frame_counts.append((nearest_int, diff))
        else:
            print(f"  [skip] pts_diff={diff}, ratio={ratio:.3f} (boundary artifact?)")
    return frame_counts

def find_flag(bits, prefix=b"H7CTF{"):
    """Brute-force offset 0-7 and polarity to find the flag prefix."""
    results = []
    for offset in range(8):
        for invert in (False, True):
            b = [1 - x for x in bits[offset:]] if invert else bits[offset:]
            data = bytearray()
            for i in range(len(b) // 8):
                chunk = b[i * 8:(i + 1) * 8]
                bval = sum(chunk[k] << (7 - k) for k in range(8))
                data.append(bval)
            idx = data.find(prefix)
            if idx != -1:
                end = data.find(b"}", idx)
                flag = data[idx:end + 1] if end != -1 else data[idx:idx + 80]
                results.append((offset, invert, flag))
                print(f"  [FLAG] offset={offset} invert={invert}: {flag.decode(errors='replace')}")
    return results

# ============================================================
# Main: load all segments (VOD + live), ordered by name
# ============================================================
def run(seg_dirs):
    all_ts_files = []
    for d in seg_dirs:
        ts_files = sorted(glob.glob(os.path.join(d, '*.ts')))
        all_ts_files.extend(ts_files)
    
    print(f"[*] Found {len(all_ts_files)} .ts files:")
    for f in all_ts_files:
        print(f"    {f}")

    # Extract PTS from each segment separately, then join
    all_pts = []
    prev_last_pts = None
    for ts_path in all_ts_files:
        with open(ts_path, 'rb') as f:
            ts_bytes = f.read()
        pts_in_seg = extract_pts_from_segment(ts_bytes)
        seg_name = os.path.basename(ts_path)
        print(f"\n  {seg_name}: {len(pts_in_seg)} PES headers")
        for pi, pts in pts_in_seg:
            print(f"    pkt {pi}: PTS={pts}")
        
        # Mark segment boundaries — we'll drop cross-segment diffs
        # by appending pts with a segment tag
        for item in pts_in_seg:
            all_pts.append((seg_name, item[0], item[1]))

    print(f"\n[*] Total PES headers: {len(all_pts)}")
    
    # Compute intra-segment PTS diffs (skip across-segment boundaries)
    all_frame_counts = []
    print("\n[*] Computing PTS differences (intra-segment only):")
    for j in range(len(all_pts) - 1):
        seg_a, _, pts_a = all_pts[j]
        seg_b, _, pts_b = all_pts[j + 1]
        
        if seg_a != seg_b:
            print(f"  [boundary] {seg_a} -> {seg_b}, skipping")
            continue
        
        diff = pts_b - pts_a
        if diff <= 0:
            continue
        ratio = diff / FRAME_UNIT
        nearest = round(ratio)
        if abs(ratio - nearest) < 0.15 and nearest > 0:
            all_frame_counts.append(nearest)
            print(f"  {seg_a}: diff={diff}, ratio={ratio:.3f} -> count={nearest}")
        else:
            print(f"  [skip] diff={diff}, ratio={ratio:.3f}")

    print(f"\n[*] Frame counts ({len(all_frame_counts)}): {all_frame_counts}")
    
    if not all_frame_counts:
        print("[!] No valid frame counts — need more data")
        return
    
    # Find unique values
    unique_counts = sorted(set(all_frame_counts))
    print(f"[*] Unique frame counts: {unique_counts}")
    
    if len(unique_counts) < 2:
        print("[!] Only one unique count — no binary signal")
        return
    
    # Map to bits: smaller count = 0, larger count = 1
    lo, hi = min(unique_counts), max(unique_counts)
    print(f"[*] Mapping: {lo} frames -> bit 0, {hi} frames -> bit 1")
    bits = [0 if c == lo else 1 if c == hi else -1 for c in all_frame_counts]
    bits = [b for b in bits if b >= 0]  # drop any ambiguous
    print(f"[*] Bit stream ({len(bits)} bits): {bits}")
    
    if len(bits) < 8:
        print("[!] Too few bits — need more segments. Keep polling.")
        return
    
    # Search for flag
    print(f"\n[*] Searching for H7CTF{{ in bit stream...")
    find_flag(bits)
    
    # If not found, print decoded bytes anyway
    print("\n[*] Raw decoded bytes (offset=0, no invert):")
    data = bytearray()
    for i in range(len(bits) // 8):
        chunk = bits[i * 8:(i + 1) * 8]
        bval = sum(chunk[k] << (7 - k) for k in range(8))
        data.append(bval)
    print(f"  Hex: {data.hex()}")
    print(f"  Text: {repr(bytes(data))}")

if __name__ == '__main__':
    seg_dirs = [
        'solutions/boardroom_av/segments',       # original VOD segments
        'solutions/boardroom_av/live_segments',  # live-polled segments
    ]
    # Filter to only existing dirs
    seg_dirs = [d for d in seg_dirs if os.path.isdir(d)]
    run(seg_dirs)
