---
challenge: worldoutter
category: web
techniques: [git_exposure, jwt_forgery]
time_to_flag: 8
status: solved
---

# WorldOutter

## Challenge Overview
- **Target URL:** `https://e131a1ef-5712-worldoutter-e225a.mystery-challenges.webverselabs-pro.com/`
- **Description:** Fantasy football web application where members can view matchups, standings, players, and scores. Accessing the `/commissioner` console is restricted to users with `role: "commissioner"` (default is `role: "member"`).
- **Flag:** `WEBVERSE{15f28017be8f140e28cc8197f2cea614}`

## Vulnerability & Exploitation
1. **Source Code / Git Exposure:**
   - Probing hidden directories revealed that the `.git/` folder was deployed and directly accessible (e.g. `/.git/HEAD`).
   - Although directory listing was disabled, Git object storage remained accessible via HTTP.
   - We read `.git/HEAD` -> `refs/heads/main` -> commit object `afb38c35f52bc28a1371f1ae4624d0d2d6fe6cbc` -> tree `94b0101379b0207f095cc1954d92c9e5f993a082`.
   - Extracted `config/secret.js` revealing `JWT_SECRET = '317e3159cbd6f230130f2b9796206afe'`.
   - Extracted `server.js` confirming that session authentication relies on an HS256 JWT cookie `wo_session`.

2. **Privilege Escalation via JWT Forgery:**
   - Forged a valid HS256 JWT cookie with claims:
     ```json
     {
       "user": "you",
       "team": "Gridiron Gophers",
       "role": "commissioner"
     }
     ```
   - Signed with secret `'317e3159cbd6f230130f2b9796206afe'`.
   - Sent request to `/commissioner` with the forged `wo_session` cookie.
   - The Commissioner console rendered the flag as the "League API key".
