from bs4 import BeautifulSoup
import sys

path = r"C:\Users\USER\.gemini\antigravity\brain\b03accc9-a76b-47d5-8e79-94ef74417664\.system_generated\steps\1996\content.md"
with open(path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

out_lines = []
infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
if infobox:
    out_lines.append("=== INFOBOX ===")
    for tr in infobox.find_all("tr"):
        out_lines.append(tr.get_text(strip=True, separator=" : "))

out_lines.append("\n=== PARAGRAPHS ===")
for p in soup.find_all("p"):
    text = p.get_text(strip=True)
    if text:
        out_lines.append(text)

with open(r"c:\Users\USER\OneDrive\Desktop\ctf\wiki_extracted.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Saved to wiki_extracted.txt successfully")
