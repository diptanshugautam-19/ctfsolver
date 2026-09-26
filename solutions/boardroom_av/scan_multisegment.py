import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

prefixes = ['boardroom', 'bridge', 'av', 'avbridge', 'av-bridge', 'meeting', 'room', 'live', 'stream', 'feed', 'api', 'v1', 'media']
suffixes = ['', 'stream', 'feed', 'live', 'audio', 'video', 'ws', 'listen', 'mic', 'out', 'leak', 'secret', 'secrets', 'room', 'bridge']

paths = set()
for p in prefixes:
    paths.add(f"/{p}")
    paths.add(f"/{p}/")
    for s in suffixes:
        if s:
            paths.add(f"/{p}/{s}")
            paths.add(f"/{p}/{s}/")
            paths.add(f"/{p}/{s}.wav")
            paths.add(f"/{p}/{s}.mp3")
            paths.add(f"/{p}/{s}.ogg")
            paths.add(f"/{p}/{s}.m3u8")
            paths.add(f"/{p}/{s}.flac")
            paths.add(f"/{p}/{s}.raw")

print(f"Testing {len(paths)} paths...")

def check(path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        req = f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(1024)
        status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status:
            return (path, status, resp)
    except Exception:
        pass
    finally:
        s.close()
    return None

with ThreadPoolExecutor(max_workers=30) as ex:
    futures = [ex.submit(check, p) for p in paths]
    for f in as_completed(futures):
        res = f.result()
        if res:
            print(f"[FOUND!] {res[0]} -> {res[1]}")
            print(res[2][:300].decode('utf-8', errors='ignore'))

print("Multi-segment scan done.")
