import boto3
import json

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
KEY_ID = "AKIAANALYST0000000000"
SECRET = "wJalrAnalystSecretKeyEXAMPLEbPxRfiCY"
REGION = "us-east-1"

session = boto3.Session(
    aws_access_key_id=KEY_ID,
    aws_secret_access_key=SECRET,
    region_name=REGION
)

print("[*] Testing STS GetCallerIdentity...")
sts = session.client("sts", endpoint_url=ENDPOINT, verify=False)
try:
    ident = sts.get_caller_identity()
    print("[+] Identity:", json.dumps(ident, indent=2, default=str))
except Exception as e:
    print("[-] STS error:", e)

print("\n[*] Testing IAM...")
iam = session.client("iam", endpoint_url=ENDPOINT, verify=False)
for action in ["get_user", "list_user_policies", "list_attached_user_policies", "list_roles", "list_policies"]:
    try:
        fn = getattr(iam, action)
        if action in ["list_user_policies", "list_attached_user_policies"]:
            res = fn(UserName="analyst")
        else:
            res = fn()
        print(f"[+] IAM {action}:", json.dumps(res, indent=2, default=str))
    except Exception as e:
        print(f"[-] IAM {action} error:", e)

print("\n[*] Testing S3...")
s3 = session.client("s3", endpoint_url=ENDPOINT, verify=False)
try:
    buckets = s3.list_buckets()
    print("[+] S3 Buckets:", json.dumps(buckets, indent=2, default=str))
except Exception as e:
    print("[-] S3 error:", e)
