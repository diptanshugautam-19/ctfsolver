#!/usr/bin/env python3
"""
flag_hunter.py - Multi-encoding recursive flag scanner with tiered confidence system.

Tiers:
  - Auto-Accept (Priority 1-2): Exact flag/ctf or platform regex matches with valid printability.
  - Candidate Review (Priority 3-5): Broad braced candidates or decoded blobs ranked by
    Shannon entropy, printable ratio, and proximity to keywords (flag, secret, key, pass).
"""

import sys
import os
import re
import math
import base64
import binascii
import urllib.parse
from collections import Counter
from typing import List, Dict, Tuple, Set

# Flag Patterns
PRIORITY_1_REGEX = re.compile(r'(?i)(?:flag|ctf)\{[^}\s]{4,}\}')
PRIORITY_2_REGEX = re.compile(r'(?:picoCTF|HTB|THM|corctf|uiuctf|DUCTF|sun\{)\{?[^}\s]+\}')
PRIORITY_5_BROAD_REGEX = re.compile(r'[A-Za-z0-9_]{2,16}\{[!-~]{6,}\}')

BASE64_BLOB_REGEX = re.compile(r'[A-Za-z0-9+/]{16,}={0,2}')
HEX_BLOB_REGEX = re.compile(r'(?:[0-9a-fA-F]{2}){12,}')

KEYWORD_REGEX = re.compile(r'(?i)(?:flag|ctf|secret|key|password|token|admin)')

# Stop words / False positive patterns (e.g. standard UUIDs, typical code snippets)
STOP_PATTERNS = [
    re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),
    re.compile(r'^([A-Z_]+)\{([A-Z_]+)\}$'),  # Code macros e.g. FOO{BAR}
]


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    printable_count = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
    return printable_count / len(data)


def rot13(text: str) -> str:
    import codecs
    return codecs.decode(text, 'rot_13')


class FlagCandidate:
    def __init__(self, flag: str, depth: int, encoding_path: List[str], tier: str, score: float = 1.0):
        self.flag = flag
        self.depth = depth
        self.encoding_path = encoding_path
        self.tier = tier  # 'AUTO_ACCEPT' or 'MANUAL_REVIEW'
        self.score = score

    def to_dict(self):
        return {
            "flag": self.flag,
            "tier": self.tier,
            "score": round(self.score, 3),
            "depth": self.depth,
            "path": " -> ".join(self.encoding_path)
        }


class FlagHunter:
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.seen_payloads: Set[bytes] = set()
        self.auto_accepts: List[FlagCandidate] = []
        self.candidates: List[FlagCandidate] = []

    def scan_raw_text(self, text: str, depth: int, path: List[str]):
        # Priority 1: Generic Flag
        for m in PRIORITY_1_REGEX.finditer(text):
            val = m.group(0)
            self.auto_accepts.append(FlagCandidate(val, depth, path, 'AUTO_ACCEPT', 1.0))

        # Priority 2: Known Platform
        for m in PRIORITY_2_REGEX.finditer(text):
            val = m.group(0)
            self.auto_accepts.append(FlagCandidate(val, depth, path, 'AUTO_ACCEPT', 0.95))

        # Priority 5: Broad braced
        for m in PRIORITY_5_BROAD_REGEX.finditer(text):
            val = m.group(0)
            if any(p.match(val) for p in STOP_PATTERNS):
                continue
            # Score this candidate
            raw_b = val.encode('utf-8', errors='ignore')
            entropy = shannon_entropy(raw_b)
            p_ratio = printable_ratio(raw_b)
            # Optimal flag entropy is between 3.0 and 5.5
            entropy_score = 1.0 - min(abs(entropy - 4.2) / 4.2, 1.0)
            
            # Keyword proximity in surrounding context
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end]
            kw_boost = 0.3 if KEYWORD_REGEX.search(context) else 0.0

            total_score = (p_ratio * 0.4) + (entropy_score * 0.3) + kw_boost
            self.candidates.append(FlagCandidate(val, depth, path, 'MANUAL_REVIEW', total_score))

    def hunt(self, data: bytes, depth: int = 0, path: List[str] = None):
        if path is None:
            path = ["raw"]
        if depth > self.max_depth or len(data) > 10_000_000:
            return
        
        digest = (hash(data), depth)
        if digest in self.seen_payloads:
            return
        self.seen_payloads.add(digest)

        text = data.decode('utf-8', errors='ignore')
        self.scan_raw_text(text, depth, path)

        if depth >= self.max_depth:
            return

        # Recursive layer decoders
        # 1. Base64
        for match in BASE64_BLOB_REGEX.finditer(text):
            blob = match.group(0)
            try:
                decoded = base64.b64decode(blob, validate=True)
                if len(decoded) >= 4 and printable_ratio(decoded) > 0.4:
                    self.hunt(decoded, depth + 1, path + [f"b64({blob[:8]}...)"])
            except Exception:
                pass

        # 2. Hex
        for match in HEX_BLOB_REGEX.finditer(text):
            h_str = match.group(0)
            try:
                decoded = binascii.unhexlify(h_str)
                if len(decoded) >= 4 and printable_ratio(decoded) > 0.4:
                    self.hunt(decoded, depth + 1, path + [f"hex({h_str[:8]}...)"])
            except Exception:
                pass

        # 3. URL-decode
        if '%' in text:
            try:
                unquoted = urllib.parse.unquote_to_bytes(text)
                if unquoted != data and len(unquoted) >= 4:
                    self.hunt(unquoted, depth + 1, path + ["urldecode"])
            except Exception:
                pass

        # 4. ROT13 (if readable text)
        if depth == 0 and printable_ratio(data) > 0.7:
            try:
                r13 = rot13(text).encode('utf-8')
                self.hunt(r13, depth + 1, path + ["rot13"])
            except Exception:
                pass

        # 5. Single-byte XOR scan (depth 0 only for efficiency)
        if depth == 0 and len(data) < 200_000:
            for k in range(1, 256):
                xored = bytes([b ^ k for b in data])
                # quick check if 'flag{' or 'ctf{' is present
                if b'flag{' in xored.lower() or b'ctf{' in xored.lower():
                    self.hunt(xored, depth + 1, path + [f"xor(0x{k:02x})"])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Multi-encoding recursive flag hunter with tiered confidence.")
    parser.add_argument("file", nargs="?", default=None, help="File to scan (or stdin if omitted)")
    parser.add_argument("--all-encodings", action="store_true", help="Enable thorough scanning across encodings")
    parser.add_argument("--max-depth", type=int, default=5, help="Max recursion depth (default: 5)")
    args = parser.parse_args()

    if args.file and os.path.exists(args.file):
        with open(args.file, "rb") as f:
            data = f.read()
    else:
        data = sys.stdin.buffer.read()

    hunter = FlagHunter(max_depth=args.max_depth)
    hunter.hunt(data)

    # Deduplicate auto_accepts
    seen_flags = set()
    unique_auto = []
    for c in hunter.auto_accepts:
        if c.flag not in seen_flags:
            seen_flags.add(c.flag)
            unique_auto.append(c)

    print("=" * 60)
    print(" FLAG HUNTER RESULTS")
    print("=" * 60)

    if unique_auto:
        print("\n[+] AUTO-ACCEPT HITS (High Confidence):")
        for hit in unique_auto:
            print(f"  * {hit.flag} | Path: {' -> '.join(hit.encoding_path)}")
    else:
        print("\n[-] No direct high-confidence flags found.")

    # Deduplicate and sort candidates by score
    unique_cand = {}
    for c in hunter.candidates:
        if c.flag not in seen_flags:
            if c.flag not in unique_cand or c.score > unique_cand[c.flag].score:
                unique_cand[c.flag] = c

    sorted_candidates = sorted(unique_cand.values(), key=lambda x: x.score, reverse=True)[:5]

    if sorted_candidates:
        print("\n[?] CANDIDATE QUEUE (Manual Review - Top Ranked):")
        for cand in sorted_candidates:
            print(f"  * [Score: {cand.score:.2f}] {cand.flag} | Path: {' -> '.join(cand.encoding_path)}")


if __name__ == "__main__":
    main()
