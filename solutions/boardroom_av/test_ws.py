import socket
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 443

for path in ['/', '/ws', '/stream', '/live', '/feed', '/bridge']:
    s = socket.create_connection((host, port), timeout=5)
    ss = ctx.wrap_socket(s, server_hostname=host)
    
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    ss.sendall(req.encode('utf-8'))
    
    try:
        resp = ss.recv(4096)
        status_line = resp.split(b'\r\n')[0].decode('utf-8', errors='ignore')
        print(f"WS test {path} -> {status_line}")
    except Exception as e:
        print(f"WS test {path} -> {e}")
    finally:
        ss.close()
