import socket
from concurrent.futures import ThreadPoolExecutor

host = 'web-17e4256823c5a05c.web.h7tex.com'

open_ports = []

def scan(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        open_ports.append(port)
        print(f"[+] OPEN: {port}")
    except Exception:
        pass
    finally:
        s.close()

# Scan common CTF ports and web ports
candidate_ports = list(range(1, 1025)) + [
    1337, 2000, 3000, 3128, 4000, 5000, 5555, 6000, 7000, 8000, 8080, 8081, 8088,
    8090, 8443, 8554, 8888, 9000, 9090, 9999, 10000, 10001, 13337, 31337, 50000
]

print(f"Scanning {len(candidate_ports)} ports on {host}...")
with ThreadPoolExecutor(max_workers=50) as ex:
    ex.map(scan, candidate_ports)

print("Scan complete. Open ports:", sorted(open_ports))
