from androguard.misc import AnalyzeAPK

a, d, dx = AnalyzeAPK("c:/Users/USER/OneDrive/Desktop/ctf/meridian-pay-3.2.1.apk/meridian-pay-3.2.1.apk")

print("=== AndroidManifest.xml ===")
print(a.get_android_manifest_axml().get_xml().decode())

print("\n=== Decompiled Classes ===")
for cls in dx.get_classes():
    cname = cls.name
    if "com/meridian/pay" in cname:
        print("\n" + "="*60)
        print(f"CLASS: {cname}")
        print("="*60)
        for method in cls.get_methods():
            m = method.get_method()
            print(f"\n--- {m.get_class_name()}->{m.get_name()}{m.get_descriptor()} ---")
            try:
                # get source
                src = method.get_source()
                if src:
                    print(src)
                else:
                    # print smali/instructions
                    code = m.get_code()
                    if code:
                        for ins in code.get_bc().get_instructions():
                            print(f"  {ins.get_name()} {ins.get_output()}")
            except Exception as e:
                print("Decompile error:", e)
