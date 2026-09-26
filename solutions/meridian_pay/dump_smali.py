from androguard.misc import AnalyzeAPK

a, d, dx = AnalyzeAPK("c:/Users/USER/OneDrive/Desktop/ctf/meridian-pay-3.2.1.apk/meridian-pay-3.2.1.apk")

with open("solutions/meridian_pay/smali_dump.txt", "w", encoding="utf-8") as out:
    for dex in d:
        for cls in dex.get_classes():
            cname = cls.get_name()
            if "com/meridian/pay" in cname:
                out.write(f"\n{'='*60}\nCLASS: {cname}\n{'='*60}\n")
                for method in cls.get_methods():
                    mname = method.get_name()
                    mdesc = method.get_descriptor()
                    out.write(f"\n--- {mname} {mdesc} ---\n")
                    code = method.get_code()
                    if code:
                        for ins in code.get_bc().get_instructions():
                            out.write(f"  {ins.get_name()} {ins.get_output()}\n")

print("[+] Wrote smali dump to solutions/meridian_pay/smali_dump.txt")
