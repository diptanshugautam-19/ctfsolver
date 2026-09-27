import urllib.request, ssl, base64, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com/boardroom/'

# ============================================================
# CHECK 1: Read m3u8 as plain text, look for hidden comments
# ============================================================
print("=== CHECK 1: m3u8 plaintext + non-standard tags ===")
req = urllib.request.Request(base + 'index.m3u8', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx, timeout=10)
m3u8_text = resp.read().decode()
print("--- m3u8 content ---")
print(m3u8_text)
print("--- end ---")

# Check for non-standard tags
standard_tags = {'#EXTM3U', '#EXT-X-VERSION', '#EXT-X-TARGETDURATION',
                 '#EXT-X-MEDIA-SEQUENCE', '#EXT-X-PLAYLIST-TYPE',
                 '#EXTINF', '#EXT-X-ENDLIST', '#EXT-X-KEY'}
print("\nNon-standard lines:")
for line in m3u8_text.splitlines():
    if line.startswith('#'):
        tag = line.split(':')[0]
        if tag not in standard_tags:
            print(f"  NON-STANDARD: {line!r}")
    elif line.strip() and not line.endswith('.ts'):
        print(f"  UNUSUAL: {line!r}")

# Check for EXT-X-KEY (AES-128 encryption)
if '#EXT-X-KEY' in m3u8_text:
    print("\n[!] EXT-X-KEY found - segments may be encrypted!")
    for line in m3u8_text.splitlines():
        if '#EXT-X-KEY' in line:
            print(f"  {line}")
else:
    print("\n  No EXT-X-KEY — segments are unencrypted")

# ============================================================
# CHECK 2: Grep all collected data for flag in many encodings
# ============================================================
print("\n\n=== CHECK 2: Blind grep across all artifacts ===")

# Build the blob
blob = m3u8_text.encode()
for i in range(6):
    with open(f'solutions/boardroom_av/segments/seg_{i:03d}.ts', 'rb') as f:
        blob += f.read()
print(f"Total blob: {len(blob)} bytes")

# Pattern list
patterns = [
    (b'H7CTF{', 'plaintext'),
    (base64.b64encode(b'H7CTF{')[:8], 'base64'),
    (b'H7CTF{'.hex().encode(), 'hex-encoded'),
    (b'483743544600', 'hex-of-H7CTF'),   # without {
    (b'SDdDVEZ7', 'base64(H7CTF{)'),
    (b'h7ctf{', 'lowercase'),
    (b'FLAG{', 'FLAG{'),
    (b'flag{', 'flag{'),
]

for pattern, name in patterns:
    for m in re.finditer(re.escape(pattern), blob, re.IGNORECASE):
        print(f"  [{name}] at {m.start()}: {blob[m.start():m.start()+80]}")

print("  (No matches = nothing found in plaintext/base64/hex)")

# ============================================================
# CHECK 3: Master playlist and video variants
# ============================================================
print("\n\n=== CHECK 3: Master/video playlist probing ===")
variant_names = [
    'master.m3u8', 'av.m3u8', 'video.m3u8', 'playlist.m3u8',
    'chunklist.m3u8', 'hls.m3u8', 'main.m3u8', 'stream.m3u8',
    'audio.m3u8', 'combined.m3u8', 'live.m3u8', 'vod.m3u8',
    'prog_index.m3u8', 'media.m3u8', 'track.m3u8',
    # Also check for video TS files
    'video.ts', 'video_000.ts', 'vseg_000.ts', 'v_000.ts',
]

for name in variant_names:
    try:
        req = urllib.request.Request(base + name, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=3)
        content = resp.read()
        print(f"  [FOUND] {name} ({resp.status}, {resp.headers.get('Content-Type')}, {len(content)} bytes):")
        print(f"    {content[:200].decode(errors='replace')}")
    except Exception as e:
        pass

print("  (No hits = no additional playlists)")
