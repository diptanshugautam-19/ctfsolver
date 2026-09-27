import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com'

dirs = ['', 'api', 'stream', 'live', 'feed', 'audio', 'static', 'media', 'boardroom', 'bridge', 'av', 'room', 'meeting', 'assets', 'data']
names = ['', 'stream', 'live', 'feed', 'audio', 'boardroom', 'bridge', 'av', 'meeting', 'room', 'secret', 'secrets', 'flag', 'out', 'mic', 'recording', 'record', 'channel', 'sound', 'voice', 'listen', 'hear', 'notes', 'transcript', 'data', 'capture', 'leak', 'exfil', 'broadcast', 'conference']
exts = ['', '.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a', '.opus', '.webm', '.pcm', '.json', '.html', '.txt', '.raw', '.m3u8', '.ts']

paths = set()
for d in dirs:
    for n in names:
        for e in exts:
            if not n and not e:
                continue
            if d:
                p = f"/{d}/{n}{e}" if n else f"/{d}{e}"
            else:
                p = f"/{n}{e}"
            paths.add(p)

print(f"Total candidate paths to test: {len(paths)}")

found = []

def check(p):
    url = base + p
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
            return (p, resp.status, resp.headers.get('Content-Type'), resp.headers.get('Content-Length'))
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return (p, e.code, e.headers.get('Content-Type'), None)
    except Exception:
        pass
    return None

with ThreadPoolExecutor(max_workers=40) as ex:
    futures = {ex.submit(check, p): p for p in paths}
    for f in as_completed(futures):
        res = f.result()
        if res:
            print(f"[FOUND!] {res[0]} -> Status {res[1]} (Type: {res[2]}, Size: {res[3]})")
            found.append(res)

print("Scan finished. Total found:", len(found))
