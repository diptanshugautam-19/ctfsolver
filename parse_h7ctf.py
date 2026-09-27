from bs4 import BeautifulSoup

path = r"C:\Users\USER\.gemini\antigravity\brain\b03accc9-a76b-47d5-8e79-94ef74417664\.system_generated\steps\2069\content.md"
with open(path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

for a in soup.find_all("a", class_=lambda c: c and "Link--primary" in c):
    print(a.get_text(strip=True))

for tr in soup.find_all("tr"):
    tds = tr.find_all("td")
    if tds:
        print([td.get_text(strip=True) for td in tds])
