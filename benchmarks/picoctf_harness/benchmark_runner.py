"""
benchmark_runner.py - Unattended CTF Challenge Benchmark & Failure Classifier.
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Any

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BENCHMARK_DIR, "benchmark_results.jsonl")
CORPUS_DIR = os.path.join(BENCHMARK_DIR, "corpus")

ENV_ERROR_INDICATORS = [
    "ModuleNotFoundError",
    "ImportError",
    "FileNotFoundError",
    "command not found"
]


def run_challenge_benchmark(challenge_dir: str, timeout_sec: int = 60) -> Dict[str, Any]:
    challenge_dir = os.path.abspath(challenge_dir)
    chal_name = os.path.basename(challenge_dir)
    solve_script = os.path.join(challenge_dir, "solve.py")
    meta_file = os.path.join(challenge_dir, "meta.json")
    expected_flag_file = os.path.join(challenge_dir, "flag.txt")
    
    meta = {}
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            pass

    expected_flag = meta.get("expected_flag", "")
    if not expected_flag and os.path.exists(expected_flag_file):
        with open(expected_flag_file, "r", encoding="utf-8") as f:
            expected_flag = f.read().strip()

    category = meta.get("category", "rev" if "rev" in chal_name else "crypto")
    points = meta.get("points", 300)

    if not os.path.exists(solve_script):
        return {
            "challenge": chal_name,
            "category": category,
            "points": points,
            "status": "MISSING_SOLVER",
            "reason": "solve.py not found in challenge directory",
            "elapsed_seconds": 0.0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    start_time = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "solve.py"],
            cwd=challenge_dir,
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        elapsed = round(time.time() - start_time, 2)
        output = proc.stdout + proc.stderr

        # Classify outcome
        if expected_flag and expected_flag in output:
            status = "SOLVED"
            reason = "Flag match confirmed"
        elif any(err in output for err in ENV_ERROR_INDICATORS):
            status = "ENV_FAIL"
            reason = f"Missing environment dependency: {proc.stderr[:150]}"
        elif "flag{" in output.lower() or "picoctf{" in output.lower():
            status = "PARTIAL"
            reason = "Flag pattern present in output but did not match expected target"
        elif proc.returncode != 0:
            status = "EXECUTION_ERROR"
            reason = f"Exited with code {proc.returncode}: {proc.stderr[:150]}"
        else:
            status = "FALSE_NEGATIVE"
            reason = "Solver ran cleanly but expected flag was not produced"

    except subprocess.TimeoutExpired:
        elapsed = timeout_sec
        status = "TIMEOUT"
        reason = f"Execution exceeded {timeout_sec}s threshold"

    record = {
        "challenge": chal_name,
        "category": category,
        "points": points,
        "status": status,
        "reason": reason,
        "elapsed_seconds": elapsed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


def run_all_corpus(corpus_root: str = CORPUS_DIR, timeout_sec: int = 60) -> List[Dict[str, Any]]:
    corpus_root = os.path.abspath(corpus_root)
    if not os.path.exists(corpus_root):
        print(f"[-] Corpus root not found: {corpus_root}")
        return []

    records = []
    print(f"[+] Benchmarking challenges under: {corpus_root}")
    for root, dirs, files in os.walk(corpus_root):
        if "solve.py" in files:
            rec = run_challenge_benchmark(root, timeout_sec=timeout_sec)
            records.append(rec)
            print(f"  * [{rec['status']}] {rec['challenge']} ({rec['category']} - {rec['points']} pts): {rec['elapsed_seconds']}s")

    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CTF Benchmark Runner")
    parser.add_argument("--corpus", default=CORPUS_DIR, help="Path to challenge corpus")
    parser.add_argument("--timeout", type=int, default=60, help="Per-challenge timeout in seconds")
    args = parser.parse_args()

    results = run_all_corpus(args.corpus, timeout_sec=args.timeout)
    print(f"\n[+] Completed {len(results)} challenge runs.")
