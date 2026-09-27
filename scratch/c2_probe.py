import socket
import ssl
import re

host = 'web-17e4256823c5a05c.web.h7tex.com'
challenge_id = '17e4256823c5a05c'

# The Go server on port 1337 is the "attacker's" C2/exfil server
# We need to query it like the compromised AV bridge would

print("=== Querying Go server (1337) with challenge-specific paths ===")

# The AV bridge might check in using its hostname/ID
paths_to_try = [
    # Using challenge UUID
    f'/{challenge_id}',
    f'/{challenge_id}/flag',
    f'/{challenge_id}/data',
    f'/{challenge_id}/status',
    f'/{challenge_id}/result',
    
    # Common C2 beacon patterns
    '/beacon', '/checkin', '/check-in', '/check_in',
    '/poll', '/update', '/sync', '/heartbeat',
    '/cmd', '/command', '/task', '/tasks',
    '/result', '/results', '/output', '/outputs',
    '/data', '/exfil', '/upload', '/collect',
    '/get', '/fetch', '/retrieve', '/pull',
    '/flag', '/secret', '/key', '/token',
    
    # The challenge might respond to GUID-based paths
    '/web-17e4256823c5a05c',
    '/boardroom',
    '/av-bridge',
    '/bridge',
    '/implant',
    '/agent',
    
    # Try with the full domain as path component
    '/web-17e4256823c5a05c.web.h7tex.com',
    
    # Try hex-encoded paths
    f'/{challenge_id.upper()}',
    
    # Common CTF challenge paths
    '/solve', '/answer', '/submit', '/flag.txt',
    '/solution', '/hint',
    
    # Maybe it requires a specific query parameter
    '/?id=' + challenge_id,
    '/?key=' + challenge_id,
    '/?token=' + challenge_id,
    '/?flag=1',
    '/?debug=1',
    '/?admin=1',
    '/?secret=1',
]

results = {}
for path in paths_to_try:
    try:
        s = socket.create_connection((host, 1337), timeout=3)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: AV-Bridge/1.0 ({challenge_id})\r\n"
            f"X-Device-ID: {challenge_id}\r\n"
            "Connection: close\r\n\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(4096)
        s.close()
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            results[path] = (status, resp)
            print(f"  [!] {path} -> {status}")
            print(f"      {resp[:300].decode(errors='replace')}")
    except Exception as e:
        pass

if not results:
    print("  All paths returned 404")

# Now try with the m3u8 playlist to see if 1337 knows about boardroom
print("\n=== Go server: try m3u8 paths ===")
for path in ['/boardroom/index.m3u8', '/boardroom/seg_000.ts']:
    try:
        s = socket.create_connection((host, 1337), timeout=3)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Accept: application/vnd.apple.mpegurl, video/MP2T\r\n"
            "Connection: close\r\n\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(1024)
        s.close()
        status = resp.split(b'\r\n')[0].decode()
        print(f"  {path}: {status}")
        if '200' in status:
            body = resp.split(b'\r\n\r\n', 1)
            if len(body) > 1:
                print(f"    {body[1][:200].decode(errors='replace')}")
    except Exception as e:
        pass

# === Re-examine the Go server's 404 response for hints ===
print("\n=== Go server 404 response details ===")
s = socket.create_connection((host, 1337), timeout=3)
req = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
s.sendall(req.encode())
resp = b""
while True:
    chunk = s.recv(4096)
    if not chunk:
        break
    resp += chunk
s.close()
print(f"Full 404 response (hex): {resp.hex()}")
print(f"Full 404 response (text): {repr(resp)}")

# === Try the Go server with the exact User-Agent of the AV bridge ===
print("\n=== Custom User-Agent attempts on 1337 ===")
user_agents = [
    'AV-Bridge/1.0',
    'Boardroom-AV/2.0',
    'Mozilla/5.0',
    f'AV-Bridge/{challenge_id}',
    'Go-http-client/1.1',
    'python-requests/2.31.0',
    'curl/7.88.1',
    'Wget/1.21.4',
    'RTSPClient/1.0',
    'VLC/3.0.18',
    'FFmpeg/6.0',
    f'implant/{challenge_id}',
    'H7CTF-Agent/1.0',
]

for ua in user_agents:
    try:
        s = socket.create_connection((host, 1337), timeout=2)
        req = f"GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(512)
        s.close()
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  UA '{ua}': {status}")
            print(f"    {resp.decode(errors='replace')[:200]}")
    except:
        pass

print("\nDone.")
