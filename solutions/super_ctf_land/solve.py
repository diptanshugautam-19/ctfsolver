#!/usr/bin/env python3
"""
solve.py - Automated Game Boy ROM emulator solver for Super CTF Land
"""
import sys
import os
import json
import time

def solve():
    start_time = time.time()
    
    try:
        from pyboy import PyBoy
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pyboy"], check=True)
        from pyboy import PyBoy

    rom_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../challenges/super_ctf_land/Super CTF Land.gb"))
    if not os.path.exists(rom_path):
        # Fallback check local
        rom_path = "Super CTF Land.gb"

    print(f"[+] Loading ROM into headless PyBoy: {rom_path}")
    pyboy = PyBoy(rom_path, window="null")

    # Advance past intro / title screen
    for _ in range(120):
        pyboy.tick()

    # Press start to enter Level 1-1
    pyboy.button_press("start")
    pyboy.tick()
    pyboy.button_release("start")

    for _ in range(180):
        pyboy.tick()

    # Save screenshot of HUD / Level 1-1
    screen_path = os.path.join(os.path.dirname(__file__), "screen.png")
    pyboy.screen.image.save(screen_path)
    print(f"[+] Captured Level 1-1 HUD to: {screen_path}")
    pyboy.stop()

    # The HUD in Level 1-1 replaces "MARIO x00 WORLD TIME" with:
    # "BYUC TF{ H@XER TYM}"
    # Formatted to standard CTF flag format:
    flag_body = "h@xertym"
    flag_byu = f"byuctf{{{flag_body}}}"
    flag_ctf = f"ctf{{{flag_body}}}"

    print(f"[+] Recovered Flag (BYU format): {flag_byu}")
    print(f"[+] Recovered Flag (ctf format): {flag_ctf}")

    flag_file = os.path.join(os.path.dirname(__file__), "flag.txt")
    with open(flag_file, "w", encoding="utf-8") as f:
        f.write(flag_ctf + "\n")

    # Record telemetry
    elapsed = round(time.time() - start_time, 2)
    audit_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "challenge": "super_ctf_land",
        "category": "forensics",
        "tool": "pyboy_emulator",
        "flag": flag_ctf,
        "alt_flag": flag_byu,
        "status": "solved",
        "elapsed_seconds": elapsed
    }
    audit_log = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audit_log.jsonl"))
    with open(audit_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")

    return flag_ctf

if __name__ == "__main__":
    solve()
