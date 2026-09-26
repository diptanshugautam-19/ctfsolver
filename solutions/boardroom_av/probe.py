import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com'
paths = [
    '/', '/stream', '/stream.mp3', '/stream.wav', '/stream.ogg', '/live', '/audio', '/feed',
    '/radio', '/boardroom', '/meeting', '/bridge', '/av', '/robots.txt', '/index.html',
    '/api', '/status', '/source', '/listen', '/play', '/live.mp3', '/live.wav',
    '/stream.flac', '/stream.aac', '/stream.m4a', '/live.ogg', '/audio.wav', '/audio.mp3',
    '/feed.mp3', '/feed.wav', '/channel', '/room', '/mic', '/bridge.mp3', '/broadcast'
]

for p in paths:
    req = urllib.request.Request(base + p, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            print(f"[FOUND] {p} -> Status: {resp.status}, Content-Type: {resp.headers.get('Content-Type')}, Size: {resp.headers.get('Content-Length')}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[STATUS {e.code}] {p}")
    except Exception as e:
        pass

print("Scan complete.")
