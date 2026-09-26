with open("solutions/meridian_pay/smali_dump.txt", "r", encoding="utf-8") as f:
    text = f.read()

for cls_name in ["Lcom/meridian/pay/RouterActivity;", "Lcom/meridian/pay/ExportProvider;", "Lcom/meridian/pay/MainActivity;"]:
    start = text.find(f"CLASS: {cls_name}")
    end = text.find("============================================================", start + 10)
    print("=" * 60)
    print(cls_name)
    print("=" * 60)
    print(text[start:end if end != -1 else len(text)])
