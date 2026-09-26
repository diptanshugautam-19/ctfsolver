import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com'

words = [
    '', 'boardroom', 'bridge', 'av', 'stream', 'feed', 'live', 'secret', 'secrets',
    'meeting', 'door', 'room', 'audio', 'video', 'listen', 'hear', 'flag', 'flag.txt',
    'app', 'static', 'public', 'files', 'download', 'downloads', 'media', 'record',
    'recording', 'recordings', 'capture', 'data', 'packet', 'pcap', 'stream.pcap',
    'capture.pcap', 'traffic.pcap', 'out', 'output', 'leak', 'exfil', 'exfiltration',
    'mic', 'microphone', 'speaker', 'sound', 'voice', 'channel', 'broadcast',
    'client', 'server', 'challenge', 'handout', 'src', 'main', 'test', 'ws', 'wss',
    'webrtc', 'rtsp', 'icecast', 'shoutcast', 'radio', 'h7ctf', 'h7', 'feed.mp3',
    'audio.mp3', 'boardroom.mp3', 'bridge.mp3', 'av.mp3', 'meeting.mp3',
    'feed.wav', 'audio.wav', 'boardroom.wav', 'bridge.wav', 'av.wav', 'meeting.wav'
]

exts = ['', '.html', '.wav', '.mp3', '.ogg', '.flac', '.pcap', '.bin', '.txt', '.py', '.zip', '.tar.gz']

paths = set()
for w in words:
    for e in exts:
        p = f"/{w}{e}" if not w.endswith(e) else f"/{w}"
        paths.add(p)

def check_path(p):
    url = base + p
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.88.1'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            return (p, resp.status, resp.headers.get('Content-Type'), resp.headers.get('Content-Length'))
    except urllib.error.HTTPError as e:
        if e.code not in [404, 501]:
            return (p, e.code, e.headers.get('Content-Type'), None)
    except Exception:
        pass
    return None

print(f"Checking {len(paths)} paths...")
with ThreadPoolExecutor(max_workers=25) as executor:
    futures = {executor.submit(check_path, p): p for p in paths}
    for future in as_completed(futures):
        res = future.result()
        if res:
            print(f"[FOUND] {res[0]} -> Status {res[1]} (Type: {res[2]}, Length: {res[3]})")

print("Done.")
