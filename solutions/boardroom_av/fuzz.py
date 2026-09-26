import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com'

words = [
    'boardroom', 'bridge', 'av', 'stream', 'feed', 'live', 'secret', 'secrets',
    'meeting', 'door', 'room', 'audio', 'video', 'listen', 'hear', 'flag', 'flag.txt',
    'app', 'static', 'public', 'files', 'download', 'downloads', 'media', 'record',
    'recording', 'recordings', 'capture', 'data', 'packet', 'pcap', 'stream.pcap',
    'capture.pcap', 'traffic.pcap', 'out', 'output', 'leak', 'exfil', 'exfiltration',
    'mic', 'microphone', 'speaker', 'sound', 'voice', 'channel', 'broadcast'
]

extensions = ['', '.html', '.wav', '.mp3', '.ogg', '.flac', '.pcap', '.pcapng', '.raw', '.bin', '.txt', '.json', '.py']

found = []
for w in words:
    for ext in extensions:
        path = f"/{w}{ext}"
        req = urllib.request.Request(f"{base}{path}", headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=2) as resp:
                print(f"[FOUND] {path} -> {resp.status} ({resp.headers.get('Content-Type')}, {resp.headers.get('Content-Length')} bytes)")
                found.append((path, resp.status, resp.headers.get('Content-Type'), resp.headers.get('Content-Length')))
        except urllib.error.HTTPError as e:
            if e.code not in [404, 501]:
                print(f"[STATUS {e.code}] {path}")
        except Exception:
            pass

print(f"Done. Found: {found}")
