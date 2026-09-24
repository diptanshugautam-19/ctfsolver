"""
auto_decode.py - Automated Multi-Layer Cipher & Encoding Decryption Engine.
Recursively detects, unwraps, and cracks nested encodings and classical ciphers.
Zero-hallucination deterministic solver.
"""

import base64
import binascii
import html
import math
import re
import string
import sys
import urllib.parse
from typing import List, Tuple, Optional, Dict, Set

ENGLISH_FREQ = {
    'a': 0.08167, 'b': 0.01492, 'c': 0.02782, 'd': 0.04253, 'e': 0.12702,
    'f': 0.02228, 'g': 0.02015, 'h': 0.06094, 'i': 0.06966, 'j': 0.00153,
    'k': 0.00772, 'l': 0.04025, 'm': 0.02406, 'n': 0.06749, 'o': 0.07507,
    'p': 0.01929, 'q': 0.00095, 'r': 0.05987, 's': 0.06327, 't': 0.09056,
    'u': 0.02758, 'v': 0.00978, 'w': 0.02360, 'x': 0.00150, 'y': 0.01974,
    'z': 0.00074, ' ': 0.13000
}

COMMON_FLAG_PREFIXES = ('flag{', 'ctf{', 'picoctf{', 'hackthebox{', 'htb{', 'securinets{', 'dice{', 'nullcon{')
FLAG_REGEX = re.compile(r'(?:[a-zA-Z0-9_\-]+)\{[ -~]{3,100}\}', re.IGNORECASE)

MORSE_DICT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
    '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
    '---..': '8', '----.': '9', '.-.-.-': '.', '--..--': ',', '..--..': '?',
    '-.-.--': '!', '-....-': '-', '-..-.': '/', '.--.-.': '@'
}

BACON_24 = {
    'AAAAA': 'A', 'AAAAB': 'B', 'AAABA': 'C', 'AAABB': 'D', 'AABAA': 'E',
    'AABAB': 'F', 'AABBA': 'G', 'AABBB': 'H', 'ABAAA': 'I', 'ABAAB': 'K',
    'ABABA': 'L', 'ABABB': 'M', 'ABBAA': 'N', 'ABBAB': 'O', 'ABBBA': 'P',
    'ABBBB': 'Q', 'BAAAA': 'R', 'BAAAB': 'S', 'BAABA': 'T', 'BAABB': 'U',
    'BABAA': 'W', 'BABAB': 'X', 'BABBA': 'Y', 'BABBB': 'Z'
}

BACON_26 = {
    'AAAAA': 'A', 'AAAAB': 'B', 'AAABA': 'C', 'AAABB': 'D', 'AABAA': 'E',
    'AABAB': 'F', 'AABBA': 'G', 'AABBB': 'H', 'ABAAA': 'I', 'ABAAB': 'J',
    'ABABA': 'K', 'ABABB': 'L', 'ABBAA': 'M', 'ABBAB': 'N', 'ABBBA': 'O',
    'ABBBB': 'P', 'BAAAA': 'Q', 'BAAAB': 'R', 'BAABA': 'S', 'BAABB': 'T',
    'BABAA': 'U', 'BABAB': 'V', 'BABBA': 'W', 'BABBB': 'X', 'BBAAA': 'Y',
    'BBAAB': 'Z'
}


def score_text(text: str) -> float:
    """Evaluate how closely text resembles natural English / readable ASCII."""
    if not text:
        return 0.0
    score = 0.0
    printable_count = 0
    for char in text:
        c = char.lower()
        if c in ENGLISH_FREQ:
            score += ENGLISH_FREQ[c]
            printable_count += 1
        elif 32 <= ord(char) <= 126:
            score += 0.01
            printable_count += 1
        elif char in '\n\r\t':
            score += 0.005
            printable_count += 1
        else:
            score -= 0.5

    ratio = printable_count / len(text)
    if ratio < 0.85:
        return -10.0
    return score / max(1, len(text))


def try_base64(data: str) -> Optional[str]:
    cleaned = re.sub(r'\s+', '', data)
    if len(cleaned) % 4 != 0:
        cleaned += '=' * (4 - (len(cleaned) % 4))
    if not re.match(r'^[A-Za-z0-9+/]+={0,2}$', cleaned):
        return None
    try:
        raw = base64.b64decode(cleaned.encode(), validate=True)
        res = raw.decode('utf-8', errors='strict')
        if len(res) > 0 and sum(1 for c in res if ord(c) < 32 and c not in '\n\r\t') == 0:
            return res
    except Exception:
        pass
    return None


def try_base32(data: str) -> Optional[str]:
    cleaned = re.sub(r'\s+', '', data).upper()
    if len(cleaned) % 8 != 0:
        cleaned += '=' * (8 - (len(cleaned) % 8))
    if not re.match(r'^[A-Z2-7]+={0,6}$', cleaned):
        return None
    try:
        raw = base64.b32decode(cleaned.encode())
        res = raw.decode('utf-8', errors='strict')
        if len(res) > 0 and sum(1 for c in res if ord(c) < 32 and c not in '\n\r\t') == 0:
            return res
    except Exception:
        pass
    return None


def try_base85(data: str) -> Optional[str]:
    cleaned = re.sub(r'\s+', '', data)
    try:
        raw = base64.b85decode(cleaned.encode())
        res = raw.decode('utf-8', errors='strict')
        if len(res) > 0 and sum(1 for c in res if ord(c) < 32 and c not in '\n\r\t') == 0:
            return res
    except Exception:
        pass
    return None


def try_ascii85(data: str) -> Optional[str]:
    cleaned = re.sub(r'\s+', '', data)
    try:
        raw = base64.a85decode(cleaned.encode())
        res = raw.decode('utf-8', errors='strict')
        if len(res) > 0 and sum(1 for c in res if ord(c) < 32 and c not in '\n\r\t') == 0:
            return res
    except Exception:
        pass
    return None


def try_hex(data: str) -> Optional[str]:
    cleaned = re.sub(r'[\s:,0x]+', '', data)
    if len(cleaned) % 2 != 0 or not re.match(r'^[0-9a-fA-F]+$', cleaned):
        return None
    try:
        raw = bytes.fromhex(cleaned)
        res = raw.decode('utf-8', errors='strict')
        if len(res) > 0 and sum(1 for c in res if ord(c) < 32 and c not in '\n\r\t') == 0:
            return res
    except Exception:
        pass
    return None


def try_binary(data: str) -> Optional[str]:
    tokens = re.split(r'[\s,]+', data.strip())
    if all(len(t) in (7, 8) and re.match(r'^[01]+$', t) for t in tokens if t):
        try:
            chars = [chr(int(t, 2)) for t in tokens if t]
            res = ''.join(chars)
            if len(res) > 0 and all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in res):
                return res
        except Exception:
            pass

    cleaned = re.sub(r'\s+', '', data)
    if len(cleaned) >= 8 and len(cleaned) % 8 == 0 and re.match(r'^[01]+$', cleaned):
        try:
            chars = [chr(int(cleaned[i:i+8], 2)) for i in range(0, len(cleaned), 8)]
            res = ''.join(chars)
            if len(res) > 0 and all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in res):
                return res
        except Exception:
            pass
    return None


def try_decimal(data: str) -> Optional[str]:
    tokens = re.split(r'[\s,]+', data.strip())
    if len(tokens) >= 3 and all(t.isdigit() and 0 <= int(t) <= 255 for t in tokens if t):
        try:
            chars = [chr(int(t)) for t in tokens if t]
            res = ''.join(chars)
            if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in res):
                return res
        except Exception:
            pass
    return None


def try_url_decode(data: str) -> Optional[str]:
    if '%' in data:
        res = urllib.parse.unquote(data)
        if res != data:
            return res
    return None


def try_html_entities(data: str) -> Optional[str]:
    if '&' in data and ';' in data:
        res = html.unescape(data)
        if res != data:
            return res
    return None


def try_morse(data: str) -> Optional[str]:
    cleaned = data.strip()
    if not all(c in '.-/ \t\n' for c in cleaned):
        return None
    words = cleaned.split('/') if '/' in cleaned else [cleaned]
    decoded_words = []
    for word in words:
        tokens = word.strip().split()
        if not tokens:
            continue
        letters = []
        for t in tokens:
            if t in MORSE_DICT:
                letters.append(MORSE_DICT[t])
            else:
                return None
        decoded_words.append(''.join(letters))
    return ' '.join(decoded_words)


def try_rot13(data: str) -> Tuple[int, str, float]:
    """Test all 25 Caesar / ROT shifts and return the best scoring English candidate."""
    best_shift = 0
    best_text = data
    best_score = score_text(data)

    for shift in range(1, 26):
        shifted = []
        for char in data:
            if 'a' <= char <= 'z':
                shifted.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
            elif 'A' <= char <= 'Z':
                shifted.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
            else:
                shifted.append(char)
        candidate = ''.join(shifted)
        sc = score_text(candidate)
        if sc > best_score:
            best_score = sc
            best_shift = shift
            best_text = candidate

    return best_shift, best_text, best_score


def try_atbash(data: str) -> str:
    res = []
    for char in data:
        if 'a' <= char <= 'z':
            res.append(chr(ord('z') - (ord(char) - ord('a'))))
        elif 'A' <= char <= 'Z':
            res.append(chr(ord('Z') - (ord(char) - ord('A'))))
        else:
            res.append(char)
    return ''.join(res)


def try_bacon(data: str) -> Optional[str]:
    """Try decoding Baconian cipher (A/B or 0/1 or Case-based)."""
    cleaned = re.sub(r'[^a-zA-Z01]', '', data)
    if len(cleaned) < 5 or len(cleaned) % 5 != 0:
        return None
    
    # Try normalizing to A and B
    for rep_a, rep_b in [('A', 'B'), ('a', 'b'), ('0', '1')]:
        if rep_a in cleaned and rep_b in cleaned:
            norm = cleaned.replace(rep_a, 'A').replace(rep_b, 'B')
            chunks = [norm[i:i+5] for i in range(0, len(norm), 5)]
            if all(c in BACON_26 for c in chunks):
                return ''.join(BACON_26[c] for c in chunks)
            if all(c in BACON_24 for c in chunks):
                return ''.join(BACON_24[c] for c in chunks)
    return None


def single_byte_xor(raw_bytes: bytes) -> List[Tuple[int, bytes, float]]:
    """Brute forces all 256 single-byte XOR keys and scores against English."""
    results = []
    for k in range(256):
        dec = bytes([b ^ k for b in raw_bytes])
        try:
            text = dec.decode('latin-1')
            sc = score_text(text)
            if sc > 0.02:
                results.append((k, dec, sc))
        except Exception:
            continue
    results.sort(key=lambda x: x[2], reverse=True)
    return results


def recursive_decode(data: str, max_depth: int = 8, current_depth: int = 0, path: Optional[List[str]] = None) -> List[Tuple[str, List[str]]]:
    """
    Recursively tests all standard encodings up to max_depth.
    Returns list of (decoded_text, history_path).
    """
    if path is None:
        path = []
    
    solutions = []

    # Check for direct high-confidence flag match
    exact_flag = re.search(r'(?:flag|picoctf|ctf|htb|dice|nullcon)\{[ -~]{3,100}\}', data, re.IGNORECASE)
    if exact_flag:
        solutions.append((data, path + [f"FLAG_FOUND: {exact_flag.group(0)}"]))
        return solutions

    if current_depth >= max_depth:
        # Check if generic flag matches at max depth
        match = FLAG_REGEX.search(data)
        if match:
            solutions.append((data, path + [f"FLAG_FOUND: {match.group(0)}"]))
        return solutions

    decoders = [
        ("Base64", try_base64),
        ("Hex", try_hex),
        ("Binary", try_binary),
        ("Base32", try_base32),
        ("Ascii85", try_ascii85),
        ("Base85", try_base85),
        ("Decimal_ASCII", try_decimal),
        ("URL_Decode", try_url_decode),
        ("HTML_Entities", try_html_entities),
        ("Morse", try_morse),
        ("Bacon", try_bacon)
    ]

    for name, func in decoders:
        try:
            res = func(data)
            if res and res != data and len(res.strip()) > 0:
                new_path = path + [name]
                sub_solutions = recursive_decode(res, max_depth, current_depth + 1, new_path)
                if sub_solutions:
                    solutions.extend(sub_solutions)
                else:
                    sc = score_text(res)
                    if sc > 0.04 or FLAG_REGEX.search(res):
                        solutions.append((res, new_path))
        except Exception:
            pass

    # Try ROT / Caesar
    shift, rot_res, rot_sc = try_rot13(data)
    if shift != 0 and rot_sc > 0.045:
        rot_path = path + [f"Caesar_ROT{shift}"]
        if FLAG_REGEX.search(rot_res):
            solutions.append((rot_res, rot_path + ["FLAG_FOUND"]))
        else:
            sub = recursive_decode(rot_res, max_depth, current_depth + 1, rot_path)
            if sub:
                solutions.extend(sub)

    return solutions


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/auto_decode.py <ciphertext_string_or_filepath> [--xor] [--rot] [--all]")
        sys.exit(1)

    target = sys.argv[1]
    # Check if target is a file
    try:
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
    except Exception:
        content = target.strip()

    print(f"[*] Input length: {len(content)} chars")
    print(f"[*] Input preview: {content[:80]}...")

    # Immediate flag check
    flag = FLAG_REGEX.search(content)
    if flag:
        print(f"[!] Direct flag found in input: {flag.group(0)}")

    print("\n[*] Starting recursive auto-decoder cascade...")
    results = recursive_decode(content, max_depth=6)

    seen = set()
    found_flags = []
    if results:
        print(f"[+] Found {len(results)} potential decoding path(s):\n")
        for text, steps in results:
            steps_str = " -> ".join(steps)
            if steps_str in seen:
                continue
            seen.add(steps_str)
            print(f"  [Path] {steps_str}")
            flag_m = FLAG_REGEX.search(text)
            if flag_m:
                print(f"  [FLAG] {flag_m.group(0)}")
                found_flags.append(flag_m.group(0))
            else:
                preview = text.replace('\n', ' ')[:100]
                print(f"  [Text] {preview}")
            print("-" * 60)
    else:
        print("[-] No clean recursive cascade match found. Trying raw byte analysis...")

    # Single-byte XOR brute force if requested or as fallback
    if "--xor" in sys.argv or not results:
        print("[*] Running Single-Byte XOR Brute Force on raw bytes...")
        try:
            # Try parsing input as hex first, else raw ascii
            clean_hex = re.sub(r'[\s:,0x]+', '', content)
            if len(clean_hex) % 2 == 0 and re.match(r'^[0-9a-fA-F]+$', clean_hex):
                raw = bytes.fromhex(clean_hex)
            else:
                raw = content.encode('latin-1')

            xor_cands = single_byte_xor(raw)
            if xor_cands:
                print(f"[+] Top {min(5, len(xor_cands))} XOR keys:")
                for k, dec, sc in xor_cands[:5]:
                    preview = dec.decode('latin-1', errors='replace').replace('\n', ' ')[:80]
                    flag_m = FLAG_REGEX.search(preview)
                    flag_tag = f" *** FLAG: {flag_m.group(0)} ***" if flag_m else ""
                    print(f"    Key 0x{k:02x} ({k:3d}) | Score: {sc:6.3f} | {preview}{flag_tag}")
        except Exception as e:
            print(f"[-] XOR analysis error: {e}")


if __name__ == "__main__":
    main()
