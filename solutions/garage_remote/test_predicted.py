import urllib.request
import json

url = "https://web-ae0648197b3162a2.web.h7tex.com/unlock"

def test_code(code_str):
    print(f"Testing code: {code_str}")
    req = urllib.request.Request(
        url,
        data=json.dumps({"code": code_str}).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Response: {resp.status} -> {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode()}")

test_code("24ae4909888c")
