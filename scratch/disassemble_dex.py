from androguard.core.dex import DEX
from androguard.core.apk import APK

apk = APK(r'c:\Users\USER\OneDrive\Desktop\ctf\codex  ctf\meridian-pay-3.2.1.apk\meridian-pay-3.2.1.apk')
dex_raw = apk.get_dex()
d = DEX(dex_raw)

out_file = r'c:\Users\USER\OneDrive\Desktop\ctf\scratch\disassembly.txt'
with open(out_file, 'w', encoding='utf-8') as f:
    for cls in d.get_classes():
        cname = cls.get_name()
        if not cname.startswith('Lcom/meridian'):
            continue
        f.write('='*60 + '\n')
        f.write(f'Class: {cname}\n')
        f.write('='*60 + '\n')
        for method in cls.get_methods():
            f.write(f'\n  Method: {method.get_name()} {method.get_descriptor()}\n')
            code = method.get_code()
            if code:
                for ins in code.get_bc().get_instructions():
                    f.write(f'    {ins.get_name()} {ins.get_output()}\n')

print("Disassembly written to", out_file)
