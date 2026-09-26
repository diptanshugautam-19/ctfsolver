import boto3
import json
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

iam = session.client("iam", endpoint_url=ENDPOINT, verify=False)
s3 = session.client("s3", endpoint_url=ENDPOINT, verify=False)

print("[*] Reading analyst-permissions inline policy...")
try:
    p = iam.get_user_policy(UserName="analyst", PolicyName="analyst-permissions")
    print(json.dumps(p, indent=2))
except Exception as e:
    print("Error:", e)

print("\n[*] Reading ci-runner-role policies...")
try:
    p_names = iam.list_role_policies(RoleName="ci-runner-role")
    print("ci-runner-role inline policies:", p_names)
    for name in p_names.get("PolicyNames", []):
        pol = iam.get_role_policy(RoleName="ci-runner-role", PolicyName=name)
        print(f"Policy {name}:", json.dumps(pol, indent=2))
except Exception as e:
    print("Error:", e)

try:
    att = iam.list_attached_role_policies(RoleName="ci-runner-role")
    print("ci-runner-role attached policies:", att)
except Exception as e:
    print("Error:", e)

print("\n[*] Checking S3 buckets...")
buckets = [
    "deputy-analyst-scratch",
    "deputy-runner-logs",
    "deputy-flag-vault",
    "deputy-crown-vault"
]

for b in buckets:
    print(f"\n--- Bucket: {b} ---")
    try:
        objs = s3.list_objects_v2(Bucket=b)
        contents = objs.get("Contents", [])
        print(f"Objects ({len(contents)}):")
        for obj in contents:
            key = obj["Key"]
            print(f"  Key: {key} ({obj['Size']} bytes)")
            try:
                data = s3.get_object(Bucket=b, Key=key)
                body = data["Body"].read().decode(errors="replace")
                print(f"    Content: {body}")
            except Exception as e_get:
                print(f"    Get error: {e_get}")
    except Exception as e:
        print(f"List error: {e}")
