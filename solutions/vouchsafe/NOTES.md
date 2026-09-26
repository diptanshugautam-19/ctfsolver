---
challenge: vouchsafe
category: web
techniques: [webauthn-fido2, enterprise-attestation-bypass, asn1-tag-confusion, cert-policy-parsing]
time_to_flag: 15
status: solved
---

# vouchsafe

## Challenge Description
> H7 Passport is our passwordless SSO. Staff tap a passkey and they are in. The admin console behind it only opens for enterprise-attested authenticators, the corporate hardware the portal already trusts.
> Open the admin console. https://web-d83cf58e26d1e625.web.h7tex.com

## Analysis
The challenge implements a WebAuthn / FIDO2 Relying Party (RP) named H7 Passport that supports passkey registration and authentication.
Privileged actions behind `/assert/finish` are restricted to credentials enrolled at the `enterprise` tier.

### Attestation & Trust Architecture
1. For standard authenticators present in MDS3 (`mds_blob.json`), the RP validates the certificate chain against pinned roots in the metadata blob.
2. The RP includes a legacy self-enrolled enterprise authenticator path for air-gapped hardware that predates MDS registration (AAGUIDs not in MDS).
3. The attestation leaf certificate carries an enterprise policy extension:
   `id-h7-authnr-policy` (OID: `1.3.6.1.4.1.61387.2.7.4`).

```asn1
AuthenticatorPolicy ::= SEQUENCE {
    version       INTEGER,
    aaguidCount   INTEGER,
    aaguids       SEQUENCE OF OCTET STRING,
    elevated  [7] BOOLEAN OPTIONAL,
    ...           -- additional context-tagged policy flags
}
```

### Vulnerability: ASN.1 Tag Confusion in Policy Parser
- Direct inclusion of `elevated = TRUE` on context tag 7 triggers an attestation rejection check (`403 {"error":"attestation rejected"}`), as authenticators are expected to ship `elevated` as FALSE.
- In v2.1, the internal parser was migrated from positional decoding to dynamic tag calculation relative to the aaguid section:
  > "The tag assigned to the trailing policy flags is now derived relative to the aaguid section rather than hard-coded, so the parser stays stable if earlier optional fields are added or removed."
- Due to the relative offset calculation bug, when evaluating whether the authenticator is elevated, the parser checks context tag `8` instead of tag `7`.
- Supplying `tag 7` as `FALSE` (`0x87 01 00`) satisfies the validity check, while simultaneously supplying `tag 8` as `TRUE` (`0x88 01 01`) tricks the parser into reading `elevated == True`.
- The credential successfully enrolls at the `enterprise` tier:
  `{"status":"enrolled","tier":"enterprise"}`
- Authenticating via `/assert/finish` triggers the privileged action and releases the flag.

## Flag
`H7CTF{13af9631-e917-4a88-bc14-2e163208f120}`
