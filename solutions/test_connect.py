import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect(('pwn.h7tex.com', 42300))
    data = s.recv(1024)
    print("Received banner:")
    print(data.decode(errors='replace'))
    s.close()
except Exception as e:
    print(f"Connection error: {e}")
