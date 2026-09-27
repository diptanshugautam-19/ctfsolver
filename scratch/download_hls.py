import urllib.request
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com'

# Step 1: Download the m3u8 playlist
print("=== Downloading /boardroom/index.m3u8 ===")
req = urllib.request.Request(f'{base}/boardroom/index.m3u8',
                             headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, context=ctx, timeout=10)
playlist = resp.read().decode()
print(playlist)

# Step 2: Parse the m3u8 and download all segments
print("\n=== Parsing playlist for segments ===")
segments = []
for line in playlist.strip().split('\n'):
    line = line.strip()
    if line and not line.startswith('#'):
        segments.append(line)
        print(f"  Segment: {line}")

# Step 3: Download each segment
os.makedirs('solutions/boardroom_av/segments', exist_ok=True)

for seg in segments:
    if seg.startswith('http'):
        url = seg
    elif seg.startswith('/'):
        url = base + seg
    else:
        url = f'{base}/boardroom/{seg}'
    
    fname = os.path.basename(seg)
    outpath = f'solutions/boardroom_av/segments/{fname}'
    print(f"\n  Downloading: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        data = resp.read()
        with open(outpath, 'wb') as f:
            f.write(data)
        print(f"    Saved: {outpath} ({len(data)} bytes)")
        # Inspect first bytes
        print(f"    First 20 bytes hex: {data[:20].hex()}")
        print(f"    Content-Type: {resp.headers.get('Content-Type')}")
    except Exception as e:
        print(f"    Error: {e}")

# Step 4: Also check if there's a master playlist or variant streams
print("\n=== Checking for additional playlists ===")
for f in ['master.m3u8', 'stream.m3u8', 'audio.m3u8', 'video.m3u8', 
          'chunklist.m3u8', 'playlist.m3u8', 'live.m3u8']:
    try:
        req = urllib.request.Request(f'{base}/boardroom/{f}',
                                     headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=5)
        content = resp.read().decode()
        print(f"\n  Found: {f}")
        print(content)
    except:
        pass

print("\nDone.")
