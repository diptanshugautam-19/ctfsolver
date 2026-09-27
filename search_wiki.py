from bs4 import BeautifulSoup

path = r"C:\Users\USER\.gemini\antigravity\brain\b03accc9-a76b-47d5-8e79-94ef74417664\.system_generated\steps\1996\content.md"
with open(path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

for li in soup.find_all("li", id=lambda x: x and x.startswith("cite_note")):
    print(li.get_text(strip=True).encode("ascii", "replace").decode("ascii"))
