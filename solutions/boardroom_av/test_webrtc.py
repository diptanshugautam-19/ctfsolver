import socket
import json

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

paths = [
    '/', '/ws', '/websocket', '/signal', '/signaling', '/room', '/rooms',
    '/janus', '/socket.io/', '/offer', '/answer', '/ice', '/sdp',
    '/bridge', '/feed', '/stream', '/live', '/audio', '/video',
    '/session', '/connect', '/join', '/rtc', '/webrtc', '/whip', '/whep',
    '/api', '/api/v1', '/api/room', '/api/stream', '/api/signal',
    '/config', '/status', '/info'
]

methods = ['GET', 'POST']

for p in paths:
    for m in methods:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            s.connect((host, port))
            body = '{"type":"offer","sdp":"dummy"}' if m == 'POST' else ''
            content_len = len(body)
            req = (
                f"{m} {p} HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                f"User-Agent: curl/8.0\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {content_len}\r\n"
                f"Connection: close\r\n"
                f"\r\n{body}"
            )
            s.sendall(req.encode())
            resp = s.recv(2048)
            status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
            if "404" not in status and "501" not in status:
                print(f"[FOUND!] {m} {p} -> {status}")
                print(resp[:300].decode('utf-8', errors='ignore'))
        except Exception:
            pass
        finally:
            s.close()

# Test WebSocket Upgrade on all paths
print("\n--- Testing WebSocket Upgrade ---")
for p in paths:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        req = (
            f"GET {p} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            f"\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(2048)
        status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status:
            print(f"[WS SUCCESS/DIFF] GET {p} -> {status}")
            print(resp[:300].decode('utf-8', errors='ignore'))
    except Exception:
        pass
    finally:
        s.close()

print("Testing complete.")
