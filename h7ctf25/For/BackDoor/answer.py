#!/usr/bin/env python3

import re
import sys
import os

MAX_ATTEMPTS = 3

CORRECT = {
    "1": "verify.google.ads",
    "2": "http://192.168.23.1:8080/verify.exe",
    "3": "KAiZ3nThong:P@ssw0rd123@",
    "4": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\UserInit:helper.exe",
    "5": "ForensicCase01@",  # config key value
    "6": "8380ac9a0a2c3f0ef0e6a02ea542b46a25f13256bb138b8a5379341524ea7311",  # hex session key (new)
    "7": "H7Tex{s3cr3t_pr0ject}"
}

SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

def normalize_domain(s: str) -> str:
    return s.strip().lower()

def normalize_url(s: str) -> str:
    return s.strip()

def normalize_credential(s: str) -> str:
    return s.strip()

def normalize_registry(s: str) -> str:
    # keep backslashes as-is but strip whitespace
    return s.strip()

def normalize_config_key(s: str) -> str:
    return s.strip()

def normalize_sha256(s: str) -> str:
    return s.strip().lower()

def normalize_secret(s: str) -> str:
    return s.strip()

QUESTIONS = [
    {
        "id": "1",
        "text": "1) What is the attacker's domain?",
        "normalize": normalize_domain,
        "hint": "Enter domain, e.g. example.com"
    },
    {
        "id": "2",
        "text": "2) What is the malicious file stored on the attacker's server (full URL)?",
        "normalize": normalize_url,
        "hint": "Enter full URL, including http:// or https://"
    },
    {
        "id": "3",
        "text": "3) What username and password did the attacker create? (<username>:<password>)",
        "normalize": normalize_credential,
        "hint": "Format: username:password"
    },
    {
        "id": "4",
        "text": "4) The attacker activated a persistence mechanism — full registry path and filename (<path registry>:<filename>)",
        "normalize": normalize_registry,
        "hint": r"Example: HK..\...\...:filename.exe"
    },
    # NEW question inserted here as id "5"
    {
        "id": "5",
        "text": "5) What is the value of the config key?",
        "normalize": normalize_config_key,
        "hint": "Exact value string (case-sensitive)"
    },
    {
        "id": "6",
        "text": "6) What is the hex value of the session key?",
        "normalize": normalize_sha256,
        "hint": "Enter 64-hex characters (no spaces)"
    },
    {
        "id": "7",
        "text": "7) Secret value exfiltrated from the file:",
        "normalize": normalize_secret,
        "hint": "Exact secret string"
    }
]

def ask_question(q):
    qid = q["id"]
    correct = CORRECT[qid]
    normalize = q["normalize"]
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        print()
        print(q["text"])
        if q.get("hint"):
            print("Hint:", q["hint"])
        user = input("> ").rstrip("\n")
        usr_norm = normalize(user)

        # extra validation for question 6 (hex session key: 64-hex)
        if qid == "6":
            if not SHA256_RE.fullmatch(user.strip()):
                print("Invalid format: value must be 64 hex characters. Try again.")
                if attempts < MAX_ATTEMPTS:
                    print(f"Attempts left: {MAX_ATTEMPTS - attempts}")
                continue
            # compare as lowercase hex
            if usr_norm == correct.lower():
                print("Correct.")
                return True
            else:
                print("Incorrect hex value.")
        else:
            # For domains, do case-insensitive compare
            if qid == "1":
                if usr_norm == correct.lower():
                    print("Correct.")
                    return True
                else:
                    print("Incorrect domain.")
            else:
                # exact match for other answers (strip only)
                if usr_norm == correct:
                    print("Correct.")
                    return True
                else:
                    print("Incorrect.")

        if attempts < MAX_ATTEMPTS:
            print(f"Try again ({MAX_ATTEMPTS - attempts} attempts left).")
        else:
            print("No attempts left for this question. Exiting.")
            return False

def main():
    print("CTF Forensic Quiz — answer each question correctly to proceed.")
    print("You have", MAX_ATTEMPTS, "attempts per question.\n")

    for q in QUESTIONS:
        ok = ask_question(q)
        if not ok:
            print("\nQuiz failed. Goodbye.")
            sys.exit(1)

    # If all correct
    print("\nAll questions correct. Congratulations!")
    
    # Get dynamic flag from environment variable
    import os
    flag = os.environ.get("FLAG", "H7CTF{test_flag}")
    print("Flag:", flag)
    
    # Optionally print the full answers summary:
    print("\nSummary of answers:")
    for k in sorted(CORRECT.keys(), key=int):
        print(f"{k}) {CORRECT[k]}")

if __name__ == "__main__":
    main()
