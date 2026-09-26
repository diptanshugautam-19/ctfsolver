# Meridian Pay CTF — Full Session Log

## Challenge
Target: `https://web-f747413d78eddd9f.web.h7tex.com`
Description: *"Meridian Pay is a neobank that shipped in a hurry and trusts everyone: the client trusts the server, the server trusts the client, and both trust the phone underneath. Four separate cracks are hiding in that arrangement, some in the app and some in the API behind it, one flag each."*

Four cracks, one flag each. Environment: Kali Linux, shell prompt `vaibhav@kali`, decoded APK at `~/meridian_decoded`.

---

## FLAGS FOUND

**Flag #1:** `H7CTF{3cb5bf7f-294c-4342-9e39-2097850947d6}`
**Flag #2:** `H7CTF{0eec5f58-5e79-443f-8830-5ed8c600b91c}`

Both were retrieved from the same endpoint:
```
GET /api/v1/internal/promo
Headers: Authorization: Bearer <token>, X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)
```
returning:
```html
<html><body><h3>Meridian Pay - Loyalty Enrollment</h3><p>Welcome back, member 1001. Enrollment confirmation:</p><pre>H7CTF{...}</pre></body></html>
```

**Key discovery:** the flag value at this endpoint is not static — it changed between sessions (after a backend state reset/redeploy), yielding flag #2 from the *same* request that originally gave flag #1. Auth requirements: missing/invalid bearer → 401; valid bearer + wrong client header → 403; valid bearer + exact client header → 200 (with the flag embedded).

---

## API BASICS

- `GET /` → `{"service":"Meridian Pay API","version":"3.2.1"}`, `server: gunicorn`
- Required header: `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)` — exact match only, no substring/case bypass found
- `POST /api/v1/auth/device` with `{"device_id":"<anything>"}` → always returns `user_id: 1001`, name `"test"` or `"Alicia Reyes"` (varied across resets), and a valid JWT. **Any device_id is accepted** — this is the confirmed "server trusts client" device-auth bug (source of flag #1's category).
- JWT: `HS256`, payload only ever `{"sub": "1001", "iat": ..., "exp": ...}`. No role/privilege claims ever observed.
- Real endpoints that exist: `/`, `/api/v1/auth/device` (POST), `/api/v1/profile` (PATCH only — GET/PUT/DELETE = 405, Allow: OPTIONS, PATCH), `/api/v1/promo/public` (GET, no auth), `/api/v1/internal/promo` (GET, auth + header required).

---

## /api/v1/profile — MASS ASSIGNMENT (extensively tested, closed out)

Endpoint accepts arbitrary JSON fields via PATCH; response format:
```json
{"profile": {"email": "...", "name": "...", "role": "...", "tier": "..."}, "updated": ["field1", "field2"]}
```

**Confirmed:** the `profile` object in the response only ever renders 4 fields (`email`, `name`, `role`, `tier`) regardless of what else is PATCHed. Other accepted fields (`is_admin`, `internal`, `verified`, `user_id`, `scopes`, `permissions`, literal `flag`/`secret`/`notes`/etc.) show up in the `updated` list (proving the server accepted/stored them) but are never echoed back or rendered anywhere else found.

**Exhaustively tested and ruled out:**
- 30+ `role` values (admin, superadmin, root, owner, staff, god, etc.) — no effect on behavior, routing, or rendering
- 8+ `tier` values — same, no effect
- `user_id` mass-assignment for impersonation — `/internal/promo` "member 1001" line never changed regardless of user_id set on profile (identity is derived from JWT `sub`, fully decoupled from the mutable profile object)
- Various `device_id` values at `/auth/device` (root, system, svc, internal-svc, support, backend, service, ci-runner, etc.) — always resolves to `sub: 1001`, single demo account, no alternate identity found
- Method/route gating tied to role state — `GET /api/v1/profile` stayed 405 regardless of role; `OPTIONS` Allow header never changed
- Type-confusion payloads (role as object/array/null/number/bool, malformed JSON, non-object body, nested `{"profile":{...}}`) — all clean 4xx, no crash/traceback, no debug info leak
- Literal suspicious field names (`flag`, `secret_flag`, `admin_flag`, `ctf_flag`, `notes`, `internal_notes`, `debug_flag`, `reveal`, `unlock`) — all accepted into `updated` but never rendered
- Header fuzzing on `X-Meridian-Client` (case, version bump, substrings, ios/web variants, debug suffixes) — always exact-match 403 unless exact string used
- Path variants (trailing slash, case, `//`, `/./`) — normalized by Werkzeug, no bypass
- JWT `alg:none` forgery (with and without trailing dot) — cleanly rejected (401)
- JWT signature tamper (swapped `sub` keeping original signature) — cleanly rejected across subs 1, 0, 1002, 9999, "admin"
- Offline HS256 secret brute-force against a custom ~50-word list AND the full `wallarm/jwt-secrets` GitHub wordlist (103,978 entries) — **no match found**, secret is not weak/guessable
- Endpoint fuzzing: root `/FUZZ`, `/api/v1/FUZZ`, `/api/v1/internal/FUZZ`, `/api/v1/admin/FUZZ`, doc/openapi paths (`/docs`, `/redoc`, `/openapi.json`, `/swagger.json` etc.), profile sub-paths (`/profile/1001`, `/profile/me`, `/profiles`, etc.), and a second larger wordlist targeting dev/admin terms — **nothing found beyond `profile` and `internal/promo`**

**Conclusion:** mass assignment is a real, demonstrable vulnerability (arbitrary field acceptance/storage) but its "flag payoff" was never found via the profile endpoint itself — flags #1 and #2 both came from `/internal/promo`'s dynamic flag generation instead. This endpoint may be a genuine standalone confirmed-vuln without its own separate flag, or its trigger condition remains undiscovered.

---

## APK STATIC ANALYSIS (decompiled in full via androguard — apktool/jadx unavailable in sandbox)

Package: `com.meridian.pay`. All classes decompiled: `ApiClient`, `MainActivity` (+ inner classes 1-4), `Session`, `RouterActivity`, `WebViewActivity`, `ExportProvider`. No hidden strings, no additional flags, no undocumented endpoints referenced anywhere in the app code. Layout (`activity_main.xml`) only contains: "Meridian Pay" title, Server field, Connect button, Promotions button, "Share latest receipt" button — nothing hidden.

### Crack 3 (candidate): ExportProvider path traversal — CONFIRMED FROM CODE, NOT YET EXECUTED
```java
// ExportProvider.openFile()
File receiptsDir = new File(getContext().getFilesDir(), "receipts");
String path = uri.getPath();
if (path.startsWith("/files/")) path = path.substring("/files/".length());
return ParcelFileDescriptor.open(new File(receiptsDir, path), MODE_READ_ONLY);
```
No canonicalization/containment check. `new File(receiptsDir, "../../shared_prefs/session.xml")` should escape the intended root.
- Provider: `content://com.meridian.pay.export`, `exported=true`, `grantUriPermissions=true`
- Seeded file: `files/receipts/receipt-8827.txt` containing `Meridian Pay receipt / Account MP-0041-8827 / Amount: $18.42 / Status: settled` (written by `MainActivity.seedReceipts()` on first launch)
- Target traversal URI: `content://com.meridian.pay.export/files/../../shared_prefs/session.xml`
- `Session` SharedPreferences (name `"session"`) stores: `base_url`, `session_token`, `account_name`, `device_id`

### Crack 4 (candidate): WebView/deep-link header leakage — CONFIRMED FROM CODE, NOT YET EXECUTED
- `RouterActivity` (exported, handles `meridianpay://open` and `https://links.meridianpay.io/open` intents, `autoVerify=false`) reads `?url=` query param, defaults to `baseUrl + /api/v1/promo/public` if absent, launches `WebViewActivity` with that URL.
- `WebViewActivity` checks `url.startsWith(session.baseUrl())` — if true, attaches `Authorization: Bearer <token>` and `X-Meridian-Client` headers before `loadUrl()`. **`startsWith()` is not a safe origin check** (e.g. `https://trusted.example.attacker.example` would pass a naive prefix check against `https://trusted.example`).
- `Session.setBaseUrl()` (settable via MainActivity's server field) strips trailing slashes only — no validation, no allowlist.
- Exploit not yet executed — needs Android runtime to fire a crafted deep-link intent.

### Manifest summary
- `MainActivity` (launcher, exported=true), `RouterActivity` (exported=true, deep links), `WebViewActivity` (exported=false), `ExportProvider` (exported=true, grantUriPermissions=true)
- `INTERNET` permission, `allowBackup=true`, `usesCleartextTraffic=true`

---

## CURRENT BLOCKER: Android emulator setup for crack 3/4 execution

Goal: install APK on an Android runtime, then run:
```bash
adb install ~/meridian_decoded/meridian-pay-3.2.1.apk
adb shell monkey -p com.meridian.pay -c android.intent.category.LAUNCHER 1
adb shell content read --uri content://com.meridian.pay.export/files/receipt-8827.txt   # sanity check
adb shell content read --uri "content://com.meridian.pay.export/files/../../shared_prefs/session.xml"   # the actual traversal exploit
```

### Environment set up so far
- Android SDK installed at `~/Android/Sdk` (cmdline-tools, platform-tools, emulator, platform android-34, system-image google_apis/x86_64)
- AVD created: `meridian` (Pixel 5 device profile, Android 14 "UpsideDownCake", google_apis/x86_64) — located at `~/.config/.android/avd/meridian.avd` (non-default path; requires `export ANDROID_AVD_HOME=~/.config/.android/avd` for the emulator binary to find it)
- Recommended permanent env vars for `~/.bashrc`:
```bash
export ANDROID_HOME=~/Android/Sdk
export ANDROID_SDK_ROOT=~/Android/Sdk
export ANDROID_AVD_HOME=~/.config/.android/avd
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator
```

### The blocker: no hardware virtualization available inside the Kali VM
- `egrep -c '(vmx|svm)' /proc/cpuinfo` → `0`; `/dev/kvm` does not exist; `modprobe kvm_intel` → "Operation not supported"
- `dmesg | grep -i kvm` consistently shows: `kvm_intel: VMX not supported by CPU`, plus oddly `Hypervisor detected: KVM` at boot (unusual for a VirtualBox guest)
- Host confirmed to be **bare-metal Windows 11** (`systeminfo`: System Manufacturer **Acer**, Model **Predator PHN16-71**, Intel CPU) — NOT a nested-VM scenario, ruling out that theory
- Tried in order, none resolved it:
  1. Enabled "Nested VT-x/AMD-V" in VirtualBox VM settings (via `VBoxManage modifyvm "kali" --nested-hw-virt on`) — confirmed `enabled` via `showvminfo`, no change
  2. Checked/disabled Hyper-V via `bcdedit /set hypervisorlaunchtype off` + full Windows reboot — no change; `VirtualMachinePlatform` and `Microsoft-Hyper-V-Hypervisor` optional features both already `Disabled`
- **Root cause identified:** Windows 11's **Virtualization-Based Security (VBS)** is running independently of the Hyper-V feature flags:
```powershell
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard | Select-Object VirtualizationBasedSecurityStatus
# returned: 2  (Running)
```
  This is common on newer OEM laptops (ships enabled by default) and claims VT-x for its own minimal hypervisor, starving VirtualBox of real virtualization access regardless of any Hyper-V/nested-virt setting.
- Attempted fix: Windows Security → Device Security → Core Isolation panel shows **"Standard hardware security not supported"** — no Memory Integrity toggle available at all (device doesn't meet Windows' requirements for the UI to even show it, likely missing TPM 2.0 config or Secure Boot state Windows wants)
- Ran registry-based disable as a workaround (GUI toggle unavailable):
```powershell
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LsaCfgFlags /t REG_DWORD /d 0 /f
```
- **Not yet confirmed whether this took effect** — next step is reboot + recheck `VirtualizationBasedSecurityStatus`, and if still `2`, escalate to the Group Policy registry keys:
```powershell
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard" /v RequirePlatformSecurityFeatures /t REG_DWORD /d 0 /f
```

### Fallback option (recommended, not yet attempted)
Use a **real Android phone** instead of the emulator — sidesteps the entire VBS/KVM problem:
1. Settings → About Phone → tap Build Number 7x → enables Developer Options
2. Developer Options → enable USB Debugging
3. Plug into the Kali machine, `adb devices`, accept the on-phone authorization prompt
4. Run the same `adb install` / `content read` traversal commands listed above

---

## NEXT STEPS
1. Reboot after VBS registry changes and confirm `VirtualizationBasedSecurityStatus` = `0`; if not, try the Group Policy registry keys above, or consider the real-phone fallback
2. Once a working Android runtime (emulator or phone) is available: install APK, run the `ExportProvider` traversal read for flag #3
3. After that: exploit the `RouterActivity`/`WebViewActivity` deep-link header-leak bug (crack 4) — likely by setting `base_url` to an attacker-controlled server via the app's Server field, then crafting a `meridianpay://open?url=...` intent that passes the naive `startsWith()` check while pointing at a different origin, to capture the leaked bearer token
