import time
import urllib.request
import ssl
import os
import sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = 'https://web-17e4256823c5a05c.web.h7tex.com/boardroom/'
seg_dir = 'solutions/boardroom_av/live_segments'
os.makedirs(seg_dir, exist_ok=True)

seen = set()
segments = []  # list of (name, bytes)

print(f"[*] Starting live HLS polling at {time.strftime('%H:%M:%S')}")
print(f"[*] Will poll for 3 minutes. Output dir: {seg_dir}")
print(f"[*] Already have: seg_000 through seg_005 (VOD)")
print()

start_time = time.time()
poll_count = 0

while time.time() - start_time < 180:  # 3 minutes
    try:
        req = urllib.request.Request(base + 'index.m3u8', headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=5)
        m3u8_text = resp.read().decode()
        poll_count += 1

        for line in m3u8_text.splitlines():
            if line.endswith('.ts') and line not in seen:
                seen.add(line)
                try:
                    seg_req = urllib.request.Request(base + line, headers={'User-Agent': 'Mozilla/5.0'})
                    seg_resp = urllib.request.urlopen(seg_req, context=ctx, timeout=10)
                    seg_data = seg_resp.read()
                    seg_path = os.path.join(seg_dir, line)
                    with open(seg_path, 'wb') as f:
                        f.write(seg_data)
                    segments.append((line, seg_data))
                    print(f"[+] New segment: {line} ({len(seg_data)} bytes) @ {time.strftime('%H:%M:%S')}")
                    sys.stdout.flush()
                except Exception as e:
                    print(f"[-] Failed to download {line}: {e}")

        # Print current playlist on first few polls and when it changes
        if poll_count <= 2:
            print(f"[m3u8 #{poll_count}]\n{m3u8_text}")
            sys.stdout.flush()

    except Exception as e:
        print(f"[-] Poll error: {e}")

    time.sleep(1)

print(f"\n[*] Done polling. Total segments: {len(segments)}")
print(f"[*] Segment names: {[s[0] for s in segments]}")

# Save summary
with open('solutions/boardroom_av/live_segments/_manifest.txt', 'w') as f:
    for name, data in segments:
        f.write(f"{name} {len(data)}\n")
