import socket
import ssl

host = 'web-17e4256823c5a05c.web.h7tex.com'

mounts = [
    '/', '/stream', '/live', '/radio', '/feed', '/boardroom', '/audio',
    '/broadcast', '/channel', '/main', '/mount', '/air', '/onair',
    '/bridge', '/listen', '/play', '/1', '/7', '/autodj', '/meeting',
    '/av', '/avbridge', '/av-bridge', '/live.mp3', '/stream.mp3',
    '/audio.mp3', '/feed.mp3', '/boardroom.mp3', '/bridge.mp3'
]

# Test on 443 (HTTPS)
print("=== Testing 443 (HTTPS) with Icy-MetaData: 1 ===")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for m in mounts:
    s = socket.create_connection((host, 443), timeout=2.5)
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
        status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status:
            print(f"[FOUND 443] {m} -> {status}")
            print(resp[:300])
    except Exception:
        pass
    finally:
        ss.close()

# Test on 1337 (HTTP)
print("\n=== Testing 1337 (HTTP) with Icy-MetaData: 1 ===")
for m in mounts:
    s = socket.create_connection((host, 1337), timeout=2.5)
    try:
        req = (
            f"GET {m} HTTP/1.0\r\n"
            f"Host: {host}:1337\r\n"
            f"User-Agent: WinampMPEG/5.66\r\n"
            f"Accept: */*\r\n"
            f"Icy-MetaData: 1\r\n"
            f"\r\n"
        )
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status:
            print(f"[FOUND 1337] {m} -> {status}")
            print(resp[:300])
    except Exception:
        pass
    finally:
        s.close()

print("Done Icecast test.")
