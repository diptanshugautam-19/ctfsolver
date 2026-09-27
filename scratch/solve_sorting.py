import sys
import re
import base64
import hashlib

sys.path.insert(0, "tools")
from scope_guard import safe_connect

s = safe_connect("pwn.h7tex.com", 41220)
s.settimeout(5.0)

f = s.makefile("rw", buffering=1, encoding="utf-8")

banner1 = f.readline().strip()
banner2 = f.readline().strip()
print("Banner:", banner1, "|", banner2, flush=True)

solved_count = 0

while True:
    line = f.readline()
    if not line:
        print("[!] EOF encountered", flush=True)
        break
    line = line.strip()
    if not line:
        continue
    
    if "H7CTF{" in line:
        print(f"[+] FOUND FLAG: {line}", flush=True)
        break
    
    m = re.match(r"\[(\d+)/250\]\s+([^:]+):\s+(.*)", line)
    if not m:
        print(f"[?] Unexpected line: {line}", flush=True)
        # Check if flag is in subsequent lines
        rest = f.read()
        print(f"Rest: {rest}", flush=True)
        break
    
    idx_str, task, data = m.groups()
    idx = int(idx_str)
    task = task.strip().lower()
    data = data.strip()
    
    if task == "reverse":
        ans = data[::-1]
    elif task == "eval":
        ans = str(eval(data, {"__builtins__": {}}, {}))
    elif task == "b64":
        ans = base64.b64decode(data).decode("utf-8")
    elif task == "sum":
        ans = str(sum(int(x.strip()) for x in data.split(",")))
    elif task == "hex":
        ans = bytes.fromhex(data).decode("utf-8")
    elif task == "md5":
        ans = hashlib.md5(data.encode()).hexdigest()
    elif task == "sha256":
        ans = hashlib.sha256(data.encode()).hexdigest()
    elif task == "sort":
        ans = ",".join(sorted(x.strip() for x in data.split(",")))
    else:
        print(f"[!] UNKNOWN TASK at step {idx}: '{task}' with data '{data}'", flush=True)
        break
    
    f.write(str(ans) + "\n")
    f.flush()
    solved_count += 1
    if idx % 25 == 0 or idx == 1 or idx == 250:
        print(f"[*] Solved [{idx}/250] ({task})", flush=True)

print(f"Finished. Total solved: {solved_count}", flush=True)
