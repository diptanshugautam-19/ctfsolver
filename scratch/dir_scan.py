import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

host = 'web-17e4256823c5a05c.web.h7tex.com'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Use the 301 redirect detection technique to find directories
# Python SimpleHTTP redirects /dir to /dir/ for any directory that exists

# Comprehensive directory list
import itertools
import string

# Common words + CTF-specific + challenge-specific
words = [
    # Common
    'static', 'assets', 'media', 'files', 'data', 'tmp', 'temp',
    'public', 'www', 'html', 'css', 'js', 'img', 'images',
    'uploads', 'download', 'downloads', 'docs', 'doc', 'api',
    'app', 'src', 'lib', 'bin', 'etc', 'var', 'log', 'logs',
    'config', 'conf', 'settings', 'admin', 'panel', 'dashboard',
    'backup', 'backups', 'old', 'new', 'test', 'dev', 'prod',
    'staging', 'debug', 'internal', 'private', 'secret', 'secrets',
    'hidden', '.hidden', '.secret', '.private', '.data',
    # Challenge specific
    'boardroom', 'av', 'bridge', 'stream', 'feed', 'audio', 'video',
    'meeting', 'room', 'door', 'camera', 'mic', 'speaker',
    'exfil', 'leak', 'output', 'capture', 'record', 'recording',
    'live', 'broadcast', 'channel', 'radio', 'listen',
    # More directories
    'flag', 'flags', 'challenge', 'ctf', 'h7ctf', 'h7',
    'c2', 'command', 'control', 'beacon', 'callback', 'hook',
    'agent', 'implant', 'payload', 'drop', 'dropzone', 'stash',
    'vault', 'safe', 'locker', 'storage', 'store', 'cache',
    'proxy', 'relay', 'forward', 'tunnel', 'gate', 'gateway',
    # Nested under boardroom
]

# Also check inside boardroom
boardroom_subdirs = [
    'stream', 'audio', 'video', 'data', 'media', 'files',
    'segments', 'chunks', 'output', 'recordings', 'archive',
    'backup', 'config', 'logs', 'static', 'assets', 'secret',
    'exfil', 'leak', 'hidden', 'flag', 'private', 'internal',
    'av', 'bridge', 'live', 'feed', 'cache', 'tmp',
]

all_dirs = [(f'/{w}', w) for w in words]
all_dirs += [(f'/boardroom/{w}', f'boardroom/{w}') for w in boardroom_subdirs]

def check_dir(path):
    try:
        s = socket.create_connection((host, 443), timeout=3)
        ss = ctx.wrap_socket(s, server_hostname=host)
        req = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        ss.sendall(req.encode())
        resp = ss.recv(512)
        ss.close()
        status_line = resp.split(b'\r\n')[0].decode()
        if '301' in status_line or '200' in status_line:
            return (path, status_line)
        return None
    except:
        return None

found_dirs = []
with ThreadPoolExecutor(max_workers=30) as ex:
    futures = {ex.submit(check_dir, p): name for p, name in all_dirs}
    for f in as_completed(futures):
        r = f.result()
        if r:
            found_dirs.append(r)
            print(f"  [DIR] {r[0]} -> {r[1]}")

if not found_dirs:
    print("No new directories found")
else:
    print(f"\nFound {len(found_dirs)} directories")

# Now also try to find files directly (not through redirect)
# by testing common filenames at root level
print("\n=== Root-level file scan ===")
root_files = [
    'index.html', 'index.htm', 'index.php', 'index.txt',
    'flag', 'flag.txt', 'flag.html', 'flag.json',
    'robots.txt', 'sitemap.xml', '.env', 'secret.txt',
    'data.txt', 'data.json', 'config.json', 'info.txt',
    'README', 'README.md', 'README.txt', 'NOTES.txt',
    'stream.m3u8', 'live.m3u8', 'audio.m3u8', 'playlist.m3u8',
    'stream.mp3', 'stream.wav', 'audio.mp3', 'audio.wav',
    'feed.xml', 'feed.json', 'api.json',
    '.well-known/security.txt', 'security.txt',
    'crossdomain.xml', 'clientaccesspolicy.xml',
    'favicon.ico', 'manifest.json', 'sw.js',
    'package.json', 'composer.json', 'Gemfile',
    'Procfile', 'Dockerfile', 'docker-compose.yml',
    'app.py', 'main.py', 'server.py', 'run.py',
    'handler.py', 'wsgi.py', 'manage.py',
    'requirements.txt', 'Pipfile', 'setup.py',
    'Makefile', 'build.sh', 'start.sh', 'run.sh',
    '.gitignore', '.dockerignore', 'LICENSE',
    'debug', 'health', 'status', 'version',
]

def check_file(fname):
    try:
        s = socket.create_connection((host, 443), timeout=3)
        ss = ctx.wrap_socket(s, server_hostname=host)
        req = f"GET /{fname} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        ss.sendall(req.encode())
        resp = ss.recv(1024)
        ss.close()
        status_line = resp.split(b'\r\n')[0].decode()
        if '200' in status_line:
            return (fname, status_line, resp)
        return None
    except:
        return None

with ThreadPoolExecutor(max_workers=30) as ex:
    futures = {ex.submit(check_file, f): f for f in root_files}
    for f in as_completed(futures):
        r = f.result()
        if r:
            print(f"  [FILE] /{r[0]} -> {r[1]}")
            print(f"    {r[2][:300].decode(errors='replace')}")

print("\nDone.")
