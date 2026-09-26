import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

host = 'web-17e4256823c5a05c.web.h7tex.com'
paths = ['/', '/ws', '/signal', '/room', '/stream', '/feed', '/bridge', '/sdp', '/offer', '/api', '/api/stream', '/socket.io/', '/janus']

print("=== HTTPS:1337 ===")
for p in paths:
    url = f"https://{host}:1337{p}"
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            print(f"{p}: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore').strip()
        print(f"{p}: HTTP {e.code} -> {body}")
    except Exception as e:
        print(f"{p}: {e}")

print("\n=== HTTP:1337 ===")
for p in paths:
    url = f"http://{host}:1337{p}"
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.0'})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"{p}: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore').strip()
        print(f"{p}: HTTP {e.code} -> {body}")
    except Exception as e:
        print(f"{p}: {e}")
