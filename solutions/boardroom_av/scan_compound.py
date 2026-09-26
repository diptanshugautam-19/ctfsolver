import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

words1 = ['av', 'boardroom', 'meeting', 'room', 'live', 'audio', 'video', 'secret', 'quiet', 'door', 'bridge']
words2 = ['bridge', 'feed', 'stream', 'live', 'audio', 'secrets', 'room', 'channel', 'data', 'exfil', 'leak', 'listen', 'hear']
seps = ['-', '_', '', '/']

paths = set()
for w1 in words1:
    for w2 in words2:
        if w1 != w2:
            for s in seps:
                p = f"/{w1}{s}{w2}"
                paths.add(p)
                paths.add(f"{p}/")
                paths.add(f"{p}.wav")
                paths.add(f"{p}.mp3")
                paths.add(f"{p}.ogg")
                paths.add(f"{p}.flac")
                paths.add(f"{p}.m3u8")

print(f"Testing {len(paths)} compound paths...")

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

with ThreadPoolExecutor(max_workers=35) as ex:
    futures = [ex.submit(check, p) for p in paths]
    for f in as_completed(futures):
        res = f.result()
        if res:
            print(f"[FOUND!] {res[0]} -> {res[1]}")
            print(res[2][:300].decode('utf-8', errors='ignore'))

print("Compound scan complete.")
