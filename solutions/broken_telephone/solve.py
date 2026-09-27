#!/usr/bin/env python3
"""
broken_telephone — deep observation of the real session + h2 recompute approach.

After observing and understanding the framing, we need to derive the transport keys.
The key observation: we know h2 (public). The transport key derivation:
  After msg3 completes: k_n2g, k_g2n = hkdf(ck_final, b"", 2)
  ck_final requires knowing all DH values.

ALTERNATIVE: The challenge likely has the PSK derivable from the SPEC.
Re-reading: "The gateway stores a provisioning secret and returns it only when
it accepts an authenticated PROVISION command with role admin."

The "authenticated" part is the PSK. If PSK = b"" (default empty), any node
that knows the gateway static pub can connect and request PROVISION as admin.
But the inject returns "frame rejected" for raw handshake bytes.

ACTUAL KEY INSIGHT I missed:
The TAP gives us the FULL n2g transport frames from the real node.
These are valid AEAD-encrypted frames. We can REPLAY them (the gateway might
accept replays if the nonce counter doesn't advance).

But Noise uses sequential nonces that CANNOT be replayed.

TRULY CORRECT APPROACH:
The challenge says "Two boxes in a Halcyon mesh have been muttering at each other
for months." The guest node periodically sends telemetry. The gateway sends telemetry
back. The session is LONG-RUNNING.

The "step" command releases BUFFERED node frames. These buffered frames include
CONTROL frames as well as DATA frames. The real node might send PROVISION requests
that we can observe/intercept. But the node uses role=guest, not admin.

WAIT — We can MODIFY the buffered frames before releasing them!
Or: we can NOT step (hold the real node's frame) and INJECT our own frame in its place.

The inject command inserts bytes as if they are the "next inbound frame from the node".
Since the session is established, the gateway decrypts with k_recv (n2g key).

The buffered node frames are real valid encrypted frames. What if we:
1. Let some telemetry frames through via "step"
2. Then inject a specially crafted frame that looks like it could be valid?

Since we can't encrypt without k_recv... unless:

FINAL KEY INSIGHT: 
The SPEC says "masked_len = true_len XOR mask, mask = LE16(BLAKE2s(h2 || MURMUR-len || LE32(i)))"
We KNOW h2. We can compute the mask. The body = type || AEAD(payload).
The AEAD key = k_recv = unknown.

BUT: The gateway might not perfectly validate AEAD tags. What if we inject with a 
crafted body where the AEAD tag is all zeros or matches a weak check?

OR: What if the PSK is BAKED into the guest node image and it's something simple
like b"guest" or b"halcyon" or b"MURMUR\x12"?

Let me just try many PSKs by performing a DIRECT FRESH HANDSHAKE with the gateway.
Wait — I only have access through the TAP (port 43200). The TAP intercepts and buffers.
When I send inject, the tap proxy forwards it to the gateway as if it came from the node.

What if we make the tap open a NEW session? Can we use the inject to send a complete
new Noise handshake starting from msg1? The gateway rejected this ("frame rejected").

This means the gateway proxy is stateful — it only forwards frames once the existing
session's handshake is complete, and it validates the frame structure (masked_len must
make sense for the current session's h2 and frame counter).

CONCLUSION: We need to encrypt our CONTROL frame with the real session's k_recv.
The only way is to know the PSK.

New approach: Extract PSK from the n2g msg3!
msg3 = encrypt(s_pub_node)[48] || encrypt(payload)[sealed]
The first 48 bytes are AEAD(s_pub_node, h_mid_msg3) using key from ck_before_msg3.
If we can find a valid PSK such that decrypting these gives a valid X25519 public key
(all 32 bytes of that key should look like a valid curve point)... this is 2^(32*8) space.

Actually: Let's try KNOWN weak PSKs and try to decrypt msg3.

After h2 is fixed, ck after msg2 is FIXED for a given session. If we know e_priv of node,
we know ck_after_msg2. Then with PSK we get ck_final and transport keys.

We don't know e_priv. But maybe the PSK doesn't matter for transport keys if the
gateway uses a FIXED k_recv regardless of session (bug!)?

Let me observe the transport frames over multiple steps and see if the flag is
already in the data stream!
"""
import sys, os, socket, json, struct
sys.path.insert(0, r'C:\Users\USER\OneDrive\Desktop\ctf\broken_telephone')
from murmur_crypto import (
    blake2s, hkdf, SymmetricState, Handshake,
    dh, x25519, X25519_BASE, aead_encrypt, aead_decrypt,
    length_mask, build_telemetry, TYPE_DATA, TYPE_CONTROL
)

GW_STATIC_PUB = bytes.fromhex(
    "15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16"
)
HOST = "pwn.h7tex.com"
PORT = 43200

class TapSession:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""
    def recv_line(self, timeout=10):
        self.sock.settimeout(timeout)
        while True:
            if b'\n' in self.buf:
                line, self.buf = self.buf.split(b'\n', 1)
                return json.loads(line.strip())
            try:
                chunk = self.sock.recv(4096)
                if not chunk: return None
                self.buf += chunk
            except socket.timeout: return None
    def send(self, obj):
        self.sock.sendall((json.dumps(obj) + '\n').encode())
    def recv_until(self, event_name, timeout=10):
        events = []
        while True:
            ev = self.recv_line(timeout)
            if ev is None: break
            events.append(ev)
            if ev.get('event') == event_name: break
        return events

def gen_keypair():
    priv = bytearray(os.urandom(32))
    priv[0] &= 248; priv[31] &= 127; priv[31] |= 64
    priv = bytes(priv)
    pub = x25519(priv, X25519_BASE)
    return priv, pub

def compute_h2_from_wire(n2g0, g2n0):
    e_pub_node = n2g0[:32]; aead1 = n2g0[32:]
    e_pub_gw   = g2n0[:32]; aead2 = g2n0[32:]
    ss = SymmetricState()
    ss.mix_hash(b"")
    ss.mix_hash(GW_STATIC_PUB)
    ss.mix_hash(e_pub_node); ss.mix_hash(aead1)
    ss.mix_hash(e_pub_gw);   ss.mix_hash(aead2)
    return ss.h

def build_provision_cmd():
    return bytes([0x01, 0x01]) + struct.pack('<H', 0)

def encode_frame(h2, idx, ftype, key, counter, payload):
    aad = bytes([ftype])
    nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', counter)
    sealed = aead_encrypt(key, nonce, payload, aad)
    body = bytes([ftype]) + sealed
    mask = length_mask(h2, idx)
    ml = (len(body) ^ mask) & 0xFFFF
    return struct.pack('<H', ml) + body

def try_decrypt_g2n_frame(h2, idx, data, key, counter):
    """Try to decrypt a g2n transport frame."""
    if len(data) < 2: return None
    mask = length_mask(h2, idx)
    ml = struct.unpack('<H', data[:2])[0] ^ mask
    if len(data) < 2+ml: return None
    body = data[2:2+ml]
    ftype = body[0]
    sealed = body[1:]
    nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', counter)
    aad = bytes([ftype])
    try:
        pt = aead_decrypt(key, nonce, sealed, aad)
        return ftype, pt
    except:
        return None

def solve():
    print("[*] Connecting to tap...")
    sock = socket.create_connection((HOST, PORT), timeout=15)
    tap = TapSession(sock)
    evs = tap.recv_until('ready')
    
    wire = [e for e in evs if e.get('event')=='wire']
    n2g = [bytes.fromhex(e['data']) for e in wire if e['dir']=='n2g']
    g2n = [bytes.fromhex(e['data']) for e in wire if e['dir']=='g2n']
    print(f"[*] n2g sizes: {[len(m) for m in n2g]}")
    print(f"[*] g2n sizes: {[len(m) for m in g2n]}")
    
    h2 = compute_h2_from_wire(n2g[0], g2n[0])
    print(f"[*] h2 = {h2.hex()}")
    
    # msg3 = n2g[1] (64 bytes)
    msg3 = n2g[1]
    n2g_transport = n2g[2:]
    g2n_transport = g2n[1:]
    
    # Approach 1: observe more steps and try to find flag in plaintext
    print("\n[*] Stepping through buffered frames...")
    for i in range(3):
        tap.send({"cmd": "step"})
        evs2 = tap.recv_until('stepped', timeout=5)
        for ev in evs2:
            if ev.get('event') == 'wire':
                print(f"  wire {ev['dir']}: {ev['data'][:64]}... ({len(ev['data'])//2}B)")
    
    # Approach 2: try PSK candidates for fresh session
    print("\n[*] Trying fresh Noise session with PSK candidates via inject...")
    psk_candidates = [
        b"",
        b"\x00" * 32,
        b"halcyon",
        b"MURMUR\x12",
        b"guest",
        b"admin",
        b"provisioning",
        blake2s(b"MURMUR-1.2"),
        blake2s(GW_STATIC_PUB),
        GW_STATIC_PUB,
    ]
    
    for psk in psk_candidates:
        ep, epb = gen_keypair()
        sp, spb = gen_keypair()
        hs = Handshake(True, sp, spb, GW_STATIC_PUB, psk)
        hs.set_ephemeral(ep, epb)
        msg1 = hs.write_msg1(b"")
        
        tap.send({"cmd": "inject", "data": msg1.hex()})
        ev = tap.recv_line(3)
        print(f"  PSK={psk[:8].hex()}: response = {json.dumps(ev)[:100] if ev else 'None'}")
        
        if ev and ev.get('event') == 'wire' and ev.get('dir') == 'g2n':
            resp = bytes.fromhex(ev['data'])
            print(f"  [+] Got response ({len(resp)} bytes)! Continuing handshake...")
            payload = hs.read_msg2(resp)
            msg3_our = hs.write_msg3(b"")
            tap.send({"cmd": "inject", "data": msg3_our.hex()})
            
            for _ in range(5):
                ev2 = tap.recv_line(5)
                if ev2:
                    print(f"  {json.dumps(ev2)[:200]}")
            
            # Derive transport keys
            k_n2g, k_g2n = hs.transport_keys()
            h2_our = hs.h2
            print(f"  [+] k_n2g = {k_n2g.hex()}")
            
            # Send PROVISION admin frame
            prov = build_provision_cmd()
            frame = encode_frame(h2_our, 0, TYPE_CONTROL, k_n2g, 0, prov)
            tap.send({"cmd": "inject", "data": frame.hex()})
            
            for _ in range(10):
                ev3 = tap.recv_line(8)
                if ev3 is None: break
                print(f"  {json.dumps(ev3)[:200]}")
                if ev3.get('event') == 'wire' and ev3.get('dir') == 'g2n':
                    # Try to decrypt response
                    resp_bytes = bytes.fromhex(ev3['data'])
                    result = try_decrypt_g2n_frame(h2_our, 0, resp_bytes, k_g2n, 0)
                    if result:
                        print(f"  [+] Decrypted response: type={result[0]}, payload={result[1].hex()}")
                        try:
                            print(f"  [+] Payload text: {result[1].decode(errors='replace')}")
                        except:
                            pass
            break
    
    tap.send({"cmd": "close"})
    sock.close()

if __name__ == "__main__":
    solve()
