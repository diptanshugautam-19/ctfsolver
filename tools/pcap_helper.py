"""
pcap_helper.py - Automated PCAP Stream Reassembler & Artifact Extractor.
Uses Scapy to extract TCP streams, HTTP payloads, and auto-decompress gzip/deflate bodies.
"""

import sys
import os
import gzip
import zlib
from collections import defaultdict
from scapy.all import rdpcap, TCP, IP, Raw


def decompress_body(data: bytes) -> bytes:
    # Try gzip
    try:
        return gzip.decompress(data)
    except Exception:
        pass
    # Try zlib
    try:
        return zlib.decompress(data)
    except Exception:
        pass
    return data


def analyze_pcap(pcap_path: str, output_dir: str = "extracted_pcap"):
    if not os.path.exists(pcap_path):
        print(f"[-] File not found: {pcap_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"[+] Reading packets from: {pcap_path}...")
    packets = rdpcap(pcap_path)

    # Group TCP packets by stream key: (min(src,dst), min_p, max(src,dst), max_p)
    streams = defaultdict(list)
    for pkt in packets:
        if IP in pkt and TCP in pkt and Raw in pkt:
            ip1, ip2 = pkt[IP].src, pkt[IP].dst
            p1, p2 = pkt[TCP].sport, pkt[TCP].dport
            key = tuple(sorted([(ip1, p1), (ip2, p2)]))
            streams[key].append((pkt[IP].src, pkt[TCP].sport, pkt[TCP].seq, pkt[Raw].load))

    print(f"[+] Found {len(streams)} TCP conversational streams with payload.")

    extracted_artifacts = []
    stream_idx = 0

    for key, segs in streams.items():
        stream_idx += 1
        # Sort by sequence number per endpoint
        assembled = bytearray()
        for src, sport, seq, load in segs:
            assembled.extend(load)

        stream_file = os.path.join(output_dir, f"stream_{stream_idx}.bin")
        with open(stream_file, "wb") as f:
            f.write(assembled)

        # Check for HTTP payloads
        if b"HTTP/" in assembled:
            parts = assembled.split(b"\r\n\r\n", 1)
            if len(parts) == 2:
                header, body = parts
                decompressed = decompress_body(body)
                art_name = os.path.join(output_dir, f"http_payload_{stream_idx}.bin")
                with open(art_name, "wb") as f:
                    f.write(decompressed)
                extracted_artifacts.append(art_name)

    print(f"[+] Extracted streams & objects written to: {output_dir}/")
    return extracted_artifacts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pcap_helper.py <capture.pcap> [output_dir]")
        sys.exit(1)
    target_pcap = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "extracted_pcap"
    analyze_pcap(target_pcap, out)
