with open("solutions/meridian_pay/smali_dump.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Let's search for interesting parts
print("Length of dump:", len(text))

# Let's print out ExportProvider, RouterActivity, WebViewActivity, ApiClient, MainActivity
lines = text.splitlines()
curr_class = ""
for line in lines:
    if line.startswith("CLASS: "):
        curr_class = line
        print("\n" + line)
    elif line.startswith("--- "):
        print("  " + line)
