import urllib.request
import json

url = "https://web-ae0648197b3162a2.web.h7tex.com/unlock"

def send_code(code_str):
    req = urllib.request.Request(
        url,
        data=json.dumps({"code": code_str}).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.status}, Body: {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

print("Testing Frame 0: 24ae49095081")
send_code("24ae49095081")

print("Testing Frame 7: 24ae49098185")
send_code("24ae49098185")

print("Testing dummy code: 000000000000")
send_code("000000000000")
