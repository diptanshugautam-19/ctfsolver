from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from androguard.decompiler.dad.decompile import DvMethod

apk_path = "c:/Users/USER/OneDrive/Desktop/ctf/meridian-pay-3.2.1.apk/meridian-pay-3.2.1.apk"
a = APK(apk_path)

print("=== AndroidManifest.xml ===")
print(a.get_android_manifest_axml().get_xml().decode())

d = DalvikVMFormat(a.get_dex())
dx = Analysis(d)

print("\n=== Classes in com.meridian.pay ===")
for cls in d.get_classes():
    name = cls.get_name()
    if "com/meridian/pay" in name:
        print(f"\n" + "="*40)
        print(f"CLASS: {name}")
        print("="*40)
        for method in cls.get_methods():
            print(f"\n--- METHOD: {method.get_name()} {method.get_descriptor()} ---")
            code = method.get_code()
            if code:
                bc = code.get_bc()
                for ins in bc.get_instructions():
                    print(f"  {ins.get_name()} {ins.get_output()}")
