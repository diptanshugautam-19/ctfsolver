import socket
import ssl
import re

host = 'web-17e4256823c5a05c.web.h7tex.com'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Strategy: The challenge description says the bridge was "compromised" and 
# the attacker is "riding the feed". Maybe data is hidden in the HTTP responses
# themselves, or there's a different endpoint we haven't found.

# 1. Check for HTTP response headers with hidden data  
print("=== Checking HTTP response headers for all HLS files ===")
files = ['index.m3u8', 'seg_000.ts', 'seg_001.ts', 'seg_002.ts', 
         'seg_003.ts', 'seg_004.ts', 'seg_005.ts']

for f in files:
    s = socket.create_connection((host, 443), timeout=5)
    ss = ctx.wrap_socket(s, server_hostname=host)
    req = f"GET /boardroom/{f} HTTP/1.0\r\nHost: {host}\r\n\r\n"
    ss.sendall(req.encode())
    resp = b""
    while True:
        chunk = ss.recv(4096)
        if not chunk:
            break
        resp += chunk
    ss.close()
    
    # Split headers and body
    header_end = resp.index(b'\r\n\r\n')
    headers = resp[:header_end].decode()
    body = resp[header_end+4:]
    
    print(f"\n  {f} ({len(body)} bytes):")
    for line in headers.split('\r\n'):
        if line.lower().startswith(('http/', 'server:', 'date:', 'content-length:', 'content-type:')):
            continue
        if line:
            print(f"    {line}")

# 2. Try the Squid proxy on port 80 to access /boardroom/ paths
print("\n=== Accessing /boardroom/ through Squid on port 80 ===")
for f in ['', 'index.m3u8', 'seg_000.ts']:
    s = socket.create_connection((host, 80), timeout=5)
    req = f"GET /boardroom/{f} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    s.sendall(req.encode())
    resp = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
    s.close()
    
    header_end = resp.index(b'\r\n\r\n')
    headers = resp[:header_end].decode()
    body = resp[header_end+4:]
    print(f"\n  Port 80 /boardroom/{f}:")
    for line in headers.split('\r\n'):
        print(f"    {line}")

# 3. Try the Go server on port 1337 with /boardroom/ paths  
print("\n=== Accessing /boardroom/ on port 1337 ===")
for f in ['', 'index.m3u8', 'seg_000.ts', 'stream', 'feed', 'flag',
          'exfil', 'data', 'secret']:
    s = socket.create_connection((host, 1337), timeout=3)
    req = f"GET /boardroom/{f} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    s.sendall(req.encode())
    try:
        resp = s.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  /boardroom/{f} -> {status}")
            print(f"    {resp[:200].decode(errors='replace')}")
    except:
        pass
    s.close()

# 4. Look for a live/dynamic version of the playlist
print("\n=== Checking if the playlist is dynamic (HLS live) ===")
# The playlist says VOD. But what if there's another endpoint for live?
for path in ['/boardroom/live.m3u8', '/boardroom/stream.m3u8', 
             '/boardroom/master.m3u8', '/boardroom/audio.m3u8',
             '/live/index.m3u8', '/stream/index.m3u8',
             '/boardroom/playlist.m3u8', '/boardroom/vod.m3u8']:
    try:
        s = socket.create_connection((host, 443), timeout=3)
        ss = ctx.wrap_socket(s, server_hostname=host)
        req = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        ss.sendall(req.encode())
        resp = ss.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  {path} -> {status}")
        ss.close()
    except:
        pass

# 5. Check HTTPS certificates for hidden data
print("\n=== SSL Certificate Details ===")
s = socket.create_connection((host, 443), timeout=5)
ss = ctx.wrap_socket(s, server_hostname=host)
cert = ss.getpeercert()
print(f"  Subject: {cert.get('subject')}")
print(f"  Issuer: {cert.get('issuer')}")
print(f"  SAN: {cert.get('subjectAltName')}")
print(f"  Serial: {cert.get('serialNumber')}")
ss.close()

# 6. Check for DNS-based data exfiltration hints
# The challenge mentions "walk secrets out the door" - maybe DNS
print("\n=== DNS queries for subdomains ===")
import socket as sock
subdomains = ['flag', 'secret', 'exfil', 'data', 'boardroom', 'av', 
              'bridge', 'stream', 'feed', 'admin', 'api', 'internal']
for sd in subdomains:
    try:
        result = sock.getaddrinfo(f'{sd}.web.h7tex.com', 443, type=sock.SOCK_STREAM)
        ips = set(r[4][0] for r in result)
        main_ip = set(r[4][0] for r in sock.getaddrinfo(host, 443, type=sock.SOCK_STREAM))
        if ips != main_ip:
            print(f"  {sd}.web.h7tex.com -> {ips} (different from main: {main_ip})")
    except:
        pass

print("\nDone.")
