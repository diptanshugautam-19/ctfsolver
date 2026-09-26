import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://web-17e4256823c5a05c.web.h7tex.com/'
for method in ['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT']:
    req = urllib.request.Request(
        url,
        method=method,
        headers={'User-Agent': 'curl/7.68.0', 'Content-Type': 'application/json'},
        data=b'{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' if method in ['POST', 'PUT'] else None
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            print(f"{method}: {resp.status} Server={resp.headers.get('Server')} Allow={resp.headers.get('Allow')}")
            body = resp.read()
            print("  Body snippet:", body[:200])
    except urllib.error.HTTPError as e:
        print(f"{method}: HTTP {e.code} Server={e.headers.get('Server')}")
        body = e.read()
        print("  Error Body snippet:", body[:200])
    except Exception as e:
        print(f"{method}: {e}")
