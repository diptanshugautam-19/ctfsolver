---
challenge: deskline
category: rev
techniques: [apk-decompilation, api-endpoint-extraction, direct-api-replay]
time_to_flag: 5
status: solved
---

# Deskline Challenge Writeup

## Summary
The challenge provided an Android application package (`deskline-1.6.0.apk`) and a target URL (`https://web-7b7730bbddb3fcb6.web.h7tex.com`) accompanied by the prompt:
> "Deskline runs the support desk our agents live in all day, one ticket queue that never stops refilling. Tucked in among the customer complaints is a single note marked agent-only, and the desk is quite sure you'll never reach it. So help yourself."

## Static Analysis of the APK
1. Disassembling `classes.dex` using Androguard revealed several key classes in package `com.deskline`:
   - `MainActivity`: Orchestrates authentication, queue synchronization, and renders tickets to the screen (`SELECT subject, body FROM tickets`).
   - `Session`: Manages persistent properties including `device_id` (prefixed with `dsk-`), `base_url` (defaulting to `http://10.0.2.2:8080`), and session `token`.
   - `ApiClient`: Wrapper around `HttpURLConnection` implementing `GET` and `POST` JSON requests with header `X-Deskline-Client: Deskline-Android/1.6.0`.
   - `DeskDb`: SQLite database (`deskline.db`) helper creating two tables: `tickets` and `credentials`.
     In `seedFromSync(String response)`:
     ```java
     JSONObject obj = new JSONObject(response);
     // ... populates tickets table ...
     JSONObject internal = obj.getJSONObject("internal");
     ContentValues cv2 = new ContentValues();
     cv2.put("label", internal.getString("label"));
     cv2.put("value", internal.getString("value"));
     db.insert("credentials", null, cv2);
     ```
   - `TicketProvider`: Content provider exported as `com.deskline.tickets` with SQL injection in `selection` and `sortOrder`.

2. The UI in `MainActivity.renderTickets()` intentionally only queries and shows the `tickets` table, completely hiding the `credentials` table populated from the `internal` JSON field.

## Exploitation
Instead of running the APK in an emulator to extract the SQLite database or exploit the ContentProvider, we can directly replay the API workflow against the target backend:
1. `POST /api/v1/auth/device` with header `X-Deskline-Client: Deskline-Android/1.6.0` and body `{"device_id": "dsk-<UUID>"}`.
   - Returns a JWT bearer token for the agent.
2. `GET /api/v1/sync` with `Authorization: Bearer <token>`.
   - Returns raw JSON:
     ```json
     {
       "internal": {
         "label": "vault-unseal-code",
         "value": "H7CTF{9a9d085f-57e9-493b-9afb-a035187f68d3}"
       },
       "tickets": [...]
     }
     ```

## Flag
`H7CTF{9a9d085f-57e9-493b-9afb-a035187f68d3}`
