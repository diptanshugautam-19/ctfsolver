// Server Component - reads environment variable at runtime
// Force dynamic rendering to read env vars on each request
export const dynamic = "force-dynamic";

export default function ChamberOfSecretsPage() {
  // Read flag from environment variable (set at container startup)
  const data = process.env.FLAG || "FLAG_HERE";

  // Decode the base64 flag on the server
  let revealed = "";
  try {
    const firstDecode = Buffer.from(data, "base64").toString("utf-8");
    const secondDecode = Buffer.from(firstDecode, "base64").toString("utf-8");
    revealed = secondDecode;
  } catch (e) {
    revealed = "Error decoding flag: " + (e as Error).message;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-950 via-gray-900 to-black flex items-center justify-center">
      <div className="text-center p-8">
        <div className="text-amber-300 text-2xl font-mono whitespace-pre-wrap">
          {revealed || "No flag found"}
        </div>
      </div>
    </div>
  );
}
