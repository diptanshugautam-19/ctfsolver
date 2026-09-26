import zipfile
import os

apk_path = "c:/Users/USER/OneDrive/Desktop/ctf/meridian-pay-3.2.1.apk/meridian-pay-3.2.1.apk"
out_dir = "solutions/meridian_pay/extracted"
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(apk_path, 'r') as zf:
    print("Files in APK:")
    for info in zf.infolist():
        print(f"  {info.filename} ({info.file_size} bytes)")
    zf.extractall(out_dir)

print(f"\n[+] Extracted all APK files to {out_dir}")
