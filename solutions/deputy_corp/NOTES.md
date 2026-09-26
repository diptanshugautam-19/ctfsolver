---
challenge: deputy_corp
category: cloud
techniques: [iam-reconnaissance, lambda-passrole-privesc, cross-account-assumerole, confused-deputy-external-id]
time_to_flag: 8
status: solved
---

# DeputyCorp — Cloud IAM Multi-Stage Writeup

## 1. Challenge Overview
- **Scenario:** DeputyCorp cloud deployment partner integration. Low-privilege `analyst` IAM key provided.
- **Endpoint:** `https://web-d94df0e990e63e98.web.h7tex.com`
- **Objective:** Recover all 4 flags across 4 progressive stages of cloud privilege escalation.

## 2. Attack Progression (4 Stages)

### Stage 1: Initial Reconnaissance & Scratch Bucket
- **Identity:** `arn:aws:iam::111111111111:user/analyst`
- **Policy:** `analyst-permissions` grants `s3:GetObject` / `s3:ListBucket` on `deputy-analyst-scratch`.
- **Action:** Reading `welcome.txt` yields **Flag 1**:
  `H7CTF{d6cc592f5a2f3db80718}`
- **Lead:** Onboarding notes describe a Lambda deployment setup running as `ci-runner-role`.

### Stage 2: Lambda PassRole & CI Runner Privilege Escalation
- **Vulnerability:** `analyst` has `iam:PassRole` on `arn:aws:iam::111111111111:role/ci-runner-role` combined with `lambda:CreateFunction` and `lambda:InvokeFunction`.
- **Action:**
  1. Create a Lambda function (`deploy_runner_fn`) assigned to `Role="arn:aws:iam::111111111111:role/ci-runner-role"`.
  2. Invoke the function to extract the temporary execution credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`).
  3. With `ci-runner-role`, read `deputy-runner-logs/build.log` to retrieve **Flag 2**:
     `H7CTF{28f87391f8a228110839}`

### Stage 3: Cross-Account AssumeRole (`partner-admin-role`)
- **Permission:** `ci-runner-role` has `sts:AssumeRole` on `arn:aws:iam::999999999999:role/partner-admin-role`.
- **Action:**
  1. Call `sts:AssumeRole` to jump into the partner account (`999999999999`).
  2. Access `deputy-flag-vault/flag` to retrieve **Flag 3**:
     `H7CTF{ea3e1dba8012d76e2648}`
  3. Inspect `deputy-flag-vault/partner-config.json`, discovering:
     - Hardened role: `arn:aws:iam::999999999999:role/partner-secure-role`
     - Required parameter: `ExternalId = "Dc-2026-8f31a97c4b2e"`

### Stage 4: Confused Deputy Exploitation (`ExternalId`) & Crown Vault
- **Concept:** The partner role requires an `ExternalId` parameter to mitigate the Confused Deputy problem. Having compromised the partner configuration, we possess the secret `ExternalId`.
- **Action:**
  1. Call `sts:AssumeRole` targeting `partner-secure-role` with `ExternalId="Dc-2026-8f31a97c4b2e"`.
  2. Use the resulting session to read `deputy-crown-vault/flag`, obtaining **Flag 4**:
     `H7CTF{1dbe909840d15aabdd63}`

## 3. Recovered Flags
- **Flag 1:** `H7CTF{d6cc592f5a2f3db80718}`
- **Flag 2:** `H7CTF{28f87391f8a228110839}`
- **Flag 3:** `H7CTF{ea3e1dba8012d76e2648}`
- **Flag 4:** `H7CTF{1dbe909840d15aabdd63}`
