with open("solutions/meridian_pay/smali_dump.txt", "r", encoding="utf-8") as f:
    text = f.read()

classes = text.split("============================================================\nCLASS: ")
for c in classes[1:]:
    header = c.split("\n")[0]
    for target in ["RouterActivity", "ExportProvider", "MainActivity", "ApiClient"]:
        if target in header:
            print("="*60)
            print("CLASS:", header)
            print("="*60)
            print(c)
