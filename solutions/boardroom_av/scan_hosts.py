import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

candidates = [
    'localhost', '127.0.0.1', 'tg42546d',
    'boardroom', 'boardroom.local', 'boardroom.internal', 'boardroom.ctf', 'boardroom.lan',
    'av', 'av.local', 'av.internal', 'av.ctf',
    'bridge', 'bridge.local', 'bridge.internal', 'bridge.ctf',
    'avbridge', 'avbridge.local', 'avbridge.internal', 'avbridge.ctf',
    'av-bridge', 'av-bridge.local', 'av-bridge.internal', 'av-bridge.ctf',
    'stream', 'stream.local', 'stream.internal', 'stream.ctf',
    'feed', 'feed.local', 'feed.internal',
    'meeting', 'meeting.local', 'meeting.internal',
    'media', 'media.local', 'media.internal'
]

subpaths = ['/', '/stream', '/live', '/audio', '/feed', '/bridge', '/ws']

pairs = [(h, sp) for h in candidates for sp in subpaths]

def check(pair):
    h, sp = pair
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        req = f"GET {sp} HTTP/1.1\r\nHost: {h}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status:
            return (h, sp, status, resp[:200])
    except Exception:
        pass
    finally:
        s.close()
    return None

with ThreadPoolExecutor(max_workers=30) as ex:
    futures = [ex.submit(check, p) for p in pairs]
    for f in as_completed(futures):
        res = f.result()
        if res:
            print(f"[FOUND!] Host: {res[0]} Path: {res[1]} -> {res[2]}\n{res[3]}")

print("Host scan finished.")
