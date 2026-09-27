import sys
from loguru import logger
logger.remove()

from androguard.misc import AnalyzeAPK

a, d, dx = AnalyzeAPK(r"C:\Users\USER\OneDrive\Desktop\ctf\deskline-1.6.0.apk\deskline-1.6.0.apk")

with open(r"C:\Users\USER\OneDrive\Desktop\ctf\scratch\deskline_decompiled.txt", "w", encoding="utf-8") as out:
    for cls in d[0].get_classes():
        name = cls.get_name()
        if "com/deskline" in name and not name.startswith("Lcom/deskline/R"):
            out.write(f"\n{'='*50}\nCLASS: {name}\n")
            for m in cls.get_methods():
                out.write(f"  METHOD: {m.get_name()} {m.get_descriptor()}\n")
                code = m.get_code()
                if code:
                    for ins in code.get_bc().get_instructions():
                        out.write(f"    {ins.get_name()} {ins.get_output()}\n")

print("Done dumping to deskline_decompiled.txt")
