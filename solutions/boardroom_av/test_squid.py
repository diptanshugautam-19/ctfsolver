import socket

host = 'web-17e4256823c5a05c.web.h7tex.com'

targets = [
    'http://localhost/',
    'http://localhost:80/',
    'http://localhost:81/',
    'http://localhost:1337/',
    'http://localhost:8000/',
    'http://localhost:5000/',
    'http://localhost:3000/',
    'http://127.0.0.1:1337/',
    'http://127.0.0.1:8000/',
    f'http://{host}/',
    f'http://{host}:1337/'
]

for p in [80, 81]:
    print(f"=== TESTING SQUID ON PORT {p} ===")
    for t in targets:
        s = socket.create_connection((host, p), timeout=3)
        try:
            req = f"GET {t} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            s.sendall(req.encode())
            resp = s.recv(1024)
            status = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
            print(f"  {t} -> {status}")
            if "200" in status or ("404" not in status and "403" not in status and "400" not in status):
                print("    Body:", resp[:200])
        except Exception as e:
            print(f"  {t} -> {e}")
        finally:
            s.close()
