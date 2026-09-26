import socket

host = 'web-17e4256823c5a05c.web.h7tex.com'
port = 1337

probes = [
    b'hello\n',
    b'HELP\n',
    b'PING\r\n',
    b'SSH-2.0-OpenSSH_8.9\r\n',
    b'\x00\x00\x00\x00',
    b'{"action":"ping"}\n',
    b'status\n'
]

for p in probes:
    s = socket.create_connection((host, port), timeout=3)
    s.sendall(p)
    try:
        data = s.recv(1024)
        print(f"Probe {p} -> {data}")
    except Exception as e:
        print(f"Probe {p} -> {e}")
    finally:
        s.close()
