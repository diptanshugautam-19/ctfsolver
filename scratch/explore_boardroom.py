import socket
import ssl

host = 'web-17e4256823c5a05c.web.h7tex.com'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test 1: GET /boardroom/ - the directory listing
print("=== GET /boardroom/ ===")
s = socket.create_connection((host, 443), timeout=5)
ss = ctx.wrap_socket(s, server_hostname=host)
req = (
    f"GET /boardroom/ HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    f"Connection: close\r\n\r\n"
)
ss.sendall(req.encode())
resp = b""
while True:
    chunk = ss.recv(4096)
    if not chunk:
        break
    resp += chunk
ss.close()
print(resp.decode(errors='replace'))

# Test 2: Try with HTTP/1.0 to get simpler response
print("\n=== GET /boardroom/ (HTTP/1.0) ===")
s = socket.create_connection((host, 443), timeout=5)
ss = ctx.wrap_socket(s, server_hostname=host)
req = (
    f"GET /boardroom/ HTTP/1.0\r\n"
    f"Host: {host}\r\n\r\n"
)
ss.sendall(req.encode())
resp = b""
while True:
    chunk = ss.recv(4096)
    if not chunk:
        break
    resp += chunk
ss.close()
print(resp.decode(errors='replace'))
