import socket
import ssl
import re

host = 'web-17e4256823c5a05c.web.h7tex.com'

# The Go server on port 1337 - try POST requests, different content types,
# API-like paths, and websocket upgrades

print("=== Port 1337: Exhaustive path scan ===")

# Focus on API-like paths common in Go web servers
go_paths = [
    # Standard Go framework routes
    '/api', '/api/', '/api/v1', '/api/v1/', '/v1/', '/v2/',
    '/api/stream', '/api/feed', '/api/boardroom', '/api/audio',
    '/api/data', '/api/flag', '/api/exfil', '/api/status',
    '/api/health', '/api/info', '/api/config',
    # Go fiber/gin/echo common paths
    '/health', '/healthz', '/ready', '/readyz', '/metrics',
    '/debug', '/debug/', '/debug/pprof', '/debug/pprof/',
    '/debug/vars', '/_debug', '/__debug',
    # Specific to the challenge scenario
    '/upload', '/receive', '/sink', '/collect', '/ingest',
    '/report', '/callback', '/webhook', '/hook',
    '/c2', '/command', '/beacon', '/check-in', '/checkin',
    '/gate', '/panel', '/drop', '/dropzone',
    # File-like paths
    '/flag', '/flag.txt', '/flag.html',
    '/static/', '/public/', '/assets/',
    '/index.html', '/index', '/home',
    # Try with the challenge ID
    '/17e4256823c5a05c', '/web-17e4256823c5a05c',
    # Common Go HTTP patterns
    '/ws', '/wss', '/socket', '/connect',
    # Reverse proxy / internal
    '/internal', '/admin', '/management',
    '/proxy', '/forward', '/relay',
    # Data exfil patterns
    '/submit', '/post', '/put', '/send',
    '/store', '/save', '/write', '/log',
]

for path in go_paths:
    try:
        s = socket.create_connection((host, 1337), timeout=2)
        req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  GET {path} -> {status}")
            print(f"    {resp.decode(errors='replace')[:200]}")
        s.close()
    except:
        pass

# Try POST requests
print("\n=== Port 1337: POST requests ===")
for path in ['/', '/api', '/submit', '/upload', '/data', '/exfil', '/stream',
             '/collect', '/receive', '/webhook', '/callback', '/report',
             '/flag', '/boardroom', '/c2', '/beacon']:
    try:
        s = socket.create_connection((host, 1337), timeout=2)
        body = '{"data":"test"}'
        req = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n\r\n{body}"
        )
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  POST {path} -> {status}")
            print(f"    {resp.decode(errors='replace')[:200]}")
        s.close()
    except:
        pass

# Try WebSocket upgrade on port 1337
print("\n=== Port 1337: WebSocket upgrade ===")
import base64
import hashlib
ws_key = base64.b64encode(b'test12345678test').decode()
ws_paths = ['/', '/ws', '/websocket', '/stream', '/feed', '/boardroom',
            '/audio', '/live', '/connect', '/socket']
for path in ws_paths:
    try:
        s = socket.create_connection((host, 1337), timeout=3)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {ws_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status:
            print(f"  WS {path} -> {status}")
            print(f"    {resp.decode(errors='replace')[:200]}")
        s.close()
    except:
        pass

# Try the Squid proxy on port 80 with a CONNECT to internal host:1337
print("\n=== Squid Proxy: CONNECT to various internal targets ===")
targets = [
    ('tg42546d', 443), ('tg42546d', 1337), ('tg42546d', 80),
    ('tg42546d', 81), ('tg42546d', 8080), ('tg42546d', 8000),
    ('127.0.0.1', 443), ('127.0.0.1', 1337), ('127.0.0.1', 81),
    (host, 443), (host, 1337), (host, 81),
]
for target_host, target_port in targets:
    try:
        s = socket.create_connection((host, 80), timeout=3)
        req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(512)
        status = resp.split(b'\r\n')[0].decode()
        if '200' in status:
            print(f"  [OPEN] CONNECT {target_host}:{target_port} -> {status}")
        elif '409' not in status and '403' not in status:
            print(f"  [?] CONNECT {target_host}:{target_port} -> {status}")
        s.close()
    except:
        pass

# Try Squid as forward proxy with absolute URL to internal services
print("\n=== Squid: Forward proxy to internal services ===")
internal_urls = [
    f'http://tg42546d/', f'http://tg42546d/boardroom/',
    f'http://tg42546d/boardroom/index.m3u8',
    f'http://tg42546d:443/', f'http://tg42546d:443/boardroom/',
    f'http://tg42546d:443/boardroom/index.m3u8',
    f'http://tg42546d:81/',
]
for url in internal_urls:
    try:
        s = socket.create_connection((host, 80), timeout=3)
        req = f"GET {url} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode()
        if '404' not in status and '403' not in status:
            print(f"  GET {url} -> {status}")
            print(f"    {resp.decode(errors='replace')[:300]}")
        s.close()
    except:
        pass

print("\nDone.")
