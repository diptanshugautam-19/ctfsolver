with open("solutions/meridian_pay/smali_dump.txt", "r", encoding="utf-8") as f:
    text = f.read()

classes_to_print = [
    "CLASS: Lcom/meridian/pay/ApiClient;",
    "CLASS: Lcom/meridian/pay/ExportProvider;",
    "CLASS: Lcom/meridian/pay/RouterActivity;",
    "CLASS: Lcom/meridian/pay/WebViewActivity;",
    "CLASS: Lcom/meridian/pay/Session;",
    "CLASS: Lcom/meridian/pay/MainActivity;"
]

sections = text.split("============================================================\nCLASS: ")
for sec in sections[1:]:
    header = sec.split("\n")[0]
    full_name = "CLASS: " + header
    for c in classes_to_print:
        if c in full_name:
            print(f"\n{'='*70}\n{full_name}\n{'='*70}\n")
            print(sec[:4000]) # first 4000 chars of class
