import socket
import time
import struct

host = 'web-17e4256823c5a05c.web.h7tex.com'

# Test 1: Raw TCP on port 81 - just listen without sending anything
print("=== Port 81: Raw TCP (no request, just listen) ===")
s = socket.create_connection((host, 81), timeout=5)
try:
    data = b""
    for _ in range(5):
        try:
            chunk = s.recv(4096)
            if not chunk:
                print("Connection closed by server")
                break
            data += chunk
            print(f"  Received {len(chunk)} bytes (total {len(data)})")
        except socket.timeout:
            print("  Timeout waiting for data")
            break
    if data:
        print(f"  First 100 bytes hex: {data[:100].hex()}")
        print(f"  First 50 bytes repr: {repr(data[:50])}")
        # Check for WAV/RIFF header
        if data[:4] == b'RIFF':
            print("  [!] RIFF/WAV header detected!")
        elif data[:3] == b'ID3' or data[:2] == b'\xff\xfb':
            print("  [!] MP3 data detected!")
        elif data[:4] == b'OggS':
            print("  [!] Ogg stream detected!")
        elif data[:4] == b'fLaC':
            print("  [!] FLAC header detected!")
    else:
        print("  No data received")
finally:
    s.close()

# Test 2: Try sending a newline to port 81
print("\n=== Port 81: Send newline then listen ===")
s = socket.create_connection((host, 81), timeout=5)
try:
    s.sendall(b"\n")
    time.sleep(0.5)
    data = s.recv(4096)
    print(f"  Received {len(data)} bytes: {repr(data[:100])}")
except socket.timeout:
    print("  Timeout")
finally:
    s.close()

# Test 3: Try Icecast/Shoutcast source request on port 81
print("\n=== Port 81: Icecast SOURCE request ===")
s = socket.create_connection((host, 81), timeout=3)
try:
    s.sendall(b"SOURCE /stream HTTP/1.0\r\nContent-Type: audio/mpeg\r\n\r\n")
    time.sleep(0.5)
    data = s.recv(4096)
    print(f"  Response: {repr(data[:200])}")
except socket.timeout:
    print("  Timeout")
finally:
    s.close()

# Test 4: Try Go server on 1337 with different paths and Accept: audio/*
print("\n=== Port 1337: Try with Accept: audio/* ===")
for p in ['/', '/stream', '/feed', '/live', '/audio', '/bridge', '/boardroom']:
    s = socket.create_connection((host, 1337), timeout=2)
    try:
        req = (
            f"GET {p} HTTP/1.1\r\n"
            f"Host: {host}:1337\r\n"
            f"Accept: audio/*, application/octet-stream\r\n"
            f"Icy-MetaData: 1\r\n"
            f"Connection: close\r\n\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if "404" not in status:
            print(f"  [FOUND] {p} -> {status}")
    except Exception:
        pass
    finally:
        s.close()

# Test 5: Try Icecast GET on port 443 with Icy headers
print("\n=== Port 443: Icecast-style requests ===")
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for m in ['/', '/stream', '/live', '/feed', '/boardroom', '/bridge',
          '/stream.mp3', '/live.mp3', '/audio', '/av', '/av-bridge']:
    s = socket.create_connection((host, 443), timeout=3)
    ss = ctx.wrap_socket(s, server_hostname=host)
    try:
        req = (
            f"GET {m} HTTP/1.0\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: WinampMPEG/5.66\r\n"
            f"Accept: */*\r\n"
            f"Icy-MetaData: 1\r\n"
            f"\r\n"
        )
        ss.sendall(req.encode())
        resp = ss.recv(1024)
        status = resp.split(b'\r\n')[0].decode()
        if "404" not in status:
            print(f"  [FOUND 443] {m} -> {status}")
            print(f"  {resp[:300]}")
    except Exception as e:
        pass
    finally:
        ss.close()

print("\nAll probes done.")
