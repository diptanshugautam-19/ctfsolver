import os

target_dir = r"c:\Users\USER\OneDrive\Desktop\ctf\writeup_archive"
keywords = ["height_feet", "hair_colour", "eye_colour", "a stranger arrives", "between the lines lies another name"]

for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith(('.md', '.txt', '.py', '.json')):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for kw in keywords:
                        if kw.lower() in content.lower():
                            print(f"MATCH: '{kw}' in {p}")
            except Exception:
                pass
print("Done searching writeup_archive")
