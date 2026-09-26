const https = require("https");
function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let body = "";
      res.on("data", (chunk) => body += chunk);
      res.on("end", () => resolve({ status: res.statusCode, body }));
    }).on("error", reject);
  });
}

(async () => {
  const list = await get("https://ctf.h7tex.com/api/v1/challenges");
  const challenges = JSON.parse(list.body).challenges;
  const meridian = challenges.filter((challenge) => /meridian|pay|trust|bank/i.test(JSON.stringify(challenge)));
  console.log(JSON.stringify(meridian, null, 2));
  for (const challenge of meridian) {
    for (const url of [
      `https://ctf.h7tex.com/api/v1/challenges/${challenge.id}`,
      `https://ctf.h7tex.com/api/v1/challenges/${challenge.slug}`,
    ]) {
      const result = await get(url);
      console.log(url, result.status, result.body);
    }
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
