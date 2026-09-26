import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

words = [
    '', 'stream', 'live', 'audio', 'video', 'feed', 'room', 'bridge', 'boardroom',
    'meeting', 'av', 'avbridge', 'av-bridge', 'secret', 'secrets', 'ws', 'websocket',
    'api', 'status', 'health', 'listen', 'play', 'mic', 'microphone', 'speaker',
    'sound', 'voice', 'channel', 'broadcast', 'flag', 'flag.txt', 'console',
    'admin', 'debug', 'source', 'download', 'media', 'record', 'recording',
    'conference', 'call', 'talk', 'session', 'transcribe', 'subtitles', 'captions',
    'chat', 'notes', 'transcript', 'data', 'packet', 'pcap', 'raw', 'rtp', 'rtsp',
    'webrtc', 'sdp', 'ice', 'hls', 'dash', 'm3u8', 'stream.m3u8', 'live.m3u8',
    'index.html', 'index', 'home', 'main', 'app', 'client', 'view', 'watch'
]

exts = ['', '.html', '.json', '.wav', '.mp3', '.ogg', '.flac', '.m3u8', '.ts', '.mp4', '.webm']

paths = set()
for w in words:
    for e in exts:
        p = f"/{w}{e}" if not w.endswith(e) else f"/{w}"
        paths.add(p)

def check_path(p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.5)
    try:
        s.connect((host, port))
        req = f"GET {p} HTTP/1.1\r\nHost: {host}:{port}\r\nUser-Agent: curl/8.0\r\nConnection: close\r\n\r\n"
        s.sendall(req.encode())
        resp = s.recv(4096)
        if not resp:
            return None
        status_line = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        if "404" not in status_line:
            headers = resp.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
            return (p, status_line, headers)
    except Exception:
        pass
    finally:
        s.close()
    return None

print(f"Fuzzing {len(paths)} endpoints on port {port}...")
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(check_path, p): p for p in paths}
    for future in as_completed(futures):
        res = future.result()
        if res:
            print(f"[FOUND!] {res[0]} -> {res[1]}\nHeaders:\n{res[2]}\n")

print("Done fuzzing port 1337.")
