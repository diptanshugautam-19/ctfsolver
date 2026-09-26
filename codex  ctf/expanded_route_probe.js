const https = require("https");
const base = "https://web-f747413d78eddd9f.web.h7tex.com";
const client = "MeridianPay-Android/3.2.1 (attested)";
function get(url, options = {}) {
  return new Promise((resolve, reject) => {
    const request = https.get(url, options, (response) => {
      let body = ""; response.on("data", (chunk) => body += chunk); response.on("end", () => resolve({ status: response.statusCode, body }));
    }); request.setTimeout(10000, () => request.destroy(new Error("timeout"))); request.on("error", reject);
  });
}
(async () => {
  const wordlist = await get("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/api/api-endpoints.txt");
  const authBody = JSON.stringify({ device_id: "expanded-route-probe" });
  const token = await new Promise((resolve, reject) => {
    const request = https.request(base + "/api/v1/auth/device", { method: "POST", headers: { "X-Meridian-Client": client, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(authBody) } }, (response) => {
      let body = ""; response.on("data", (chunk) => body += chunk); response.on("end", () => resolve(JSON.parse(body).token));
    }); request.on("error", reject); request.end(authBody);
  });
  const paths = new Set(wordlist.body.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith("#")));
  for (const path of [...paths]) if (path.startsWith("api/")) paths.add(path.slice(4));
  const requests = [...paths].flatMap((path) => [`/${path}`, `/api/v1/${path}`]);
  for (let index = 0; index < requests.length; index += 12) {
    const batch = await Promise.all(requests.slice(index, index + 12).map(async (path) => {
      try { return { path, ...(await get(base + path, { headers: { "X-Meridian-Client": client, Authorization: `Bearer ${token}` } })) }; }
      catch (error) { return { path, status: "error", body: error.message }; }
    }));
    for (const result of batch) if (result.status !== 404) console.log(JSON.stringify(result));
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
