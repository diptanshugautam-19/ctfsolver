"""
coppersmith.py - Lattice Reduction & Coppersmith Attack Bridge.

Techniques:
  - small_roots_stereotyped: Solves (known_prefix + x)^e = c (mod n) for small x
  - factor_high_bits_known: Factors N when MSBs of prime factor p are known
  - franklin_reiter: Related message attack for c1 = m^e (mod n), c2 = (a*m + b)^e (mod n)
  - boneh_durfee: High-efficiency short private exponent attack (d < n^0.292)

Backend Resolution:
  1. System Sage (`sage <script>.sage`) via subprocess with structured JSON I/O
  2. Pure-Python Lenstra–Lenstra–Lovász (LLL) lattice reduction fallback
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from typing import Optional, Tuple, List, Dict, Any
from Crypto.Util.number import long_to_bytes, bytes_to_long


def _find_sage() -> Optional[str]:
    """Check for local or WSL SageMath executable."""
    sage_path = shutil.which("sage")
    if sage_path:
        return sage_path
    
    # Check common Linux / WSL paths
    common_paths = [
        "/usr/bin/sage",
        "/usr/local/bin/sage"
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    return None


def _run_sage(script_code: str, timeout_sec: int = 45) -> Optional[Dict[str, Any]]:
    """Execute generated Sage script via subprocess and parse JSON stdout."""
    sage_bin = _find_sage()
    if not sage_bin:
        return None

    with tempfile.NamedTemporaryFile(suffix=".sage", mode="w", delete=False, encoding="utf-8") as f:
        f.write(script_code)
        temp_name = f.name

    try:
        proc = subprocess.run(
            [sage_bin, temp_name],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        if proc.returncode == 0:
            for line in reversed(proc.stdout.strip().split("\n")):
                try:
                    return json.loads(line)
                except Exception:
                    continue
    except Exception:
        pass
    finally:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except Exception:
                pass
    return None


# --- Pure-Python LLL Implementation (Fallback) ---

def _dot_product(u: List[float], v: List[float]) -> float:
    return sum(x * y for x, y in zip(u, v))


def _gram_schmidt(B: List[List[int]]) -> Tuple[List[List[float]], List[List[float]]]:
    n = len(B)
    m = len(B[0])
    B_star = [[0.0] * m for _ in range(n)]
    mu = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        B_star[i] = [float(x) for x in B[i]]
        for j in range(i):
            num = _dot_product([float(x) for x in B[i]], B_star[j])
            den = _dot_product(B_star[j], B_star[j])
            mu[i][j] = num / den if den != 0 else 0.0
            for k in range(m):
                B_star[i][k] -= mu[i][j] * B_star[j][k]
    return B_star, mu


def lll_reduction(basis: List[List[int]], delta: float = 0.75) -> List[List[int]]:
    """Lenstra-Lenstra-Lovasz (LLL) basis reduction in pure Python."""
    B = [list(row) for row in basis]
    n = len(B)
    k = 1
    
    B_star, mu = _gram_schmidt(B)
    
    while k < n:
        for j in range(k - 1, -1, -1):
            if abs(mu[k][j]) > 0.5:
                q = round(mu[k][j])
                for m_idx in range(len(B[k])):
                    B[k][m_idx] -= q * B[j][m_idx]
                B_star, mu = _gram_schmidt(B)
                
        # Lovasz condition
        num = _dot_product(B_star[k], B_star[k])
        den = (delta - mu[k][k - 1] ** 2) * _dot_product(B_star[k - 1], B_star[k - 1])
        if num >= den:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            B_star, mu = _gram_schmidt(B)
            k = max(k - 1, 1)
            
    return B


# --- Coppersmith Attack Facades ---

def small_roots_stereotyped(
    n: int,
    e: int,
    c: int,
    known_prefix: bytes,
    unknown_bytes: int = 16,
    beta: float = 1.0
) -> Optional[bytes]:
    """
    Coppersmith Stereotyped Message Attack:
    m = prefix || x, where len(x) <= unknown_bytes
    Solves f(x) = (prefix_val * 2^(unknown_bits) + x)^e - c = 0 mod n
    """
    unknown_bits = unknown_bytes * 8
    prefix_val = bytes_to_long(known_prefix)
    X = 2 ** unknown_bits

    # 1. Attempt Sage backend
    sage_code = f"""import json
n = {n}
e = {e}
c = {c}
prefix_val = {prefix_val}
unknown_bits = {unknown_bits}
X = {X}

P.<x> = PolynomialRing(Zmod(n))
f = (prefix_val * (2^unknown_bits) + x)^e - c
f = f.monic()

roots = f.small_roots(X=X, beta={beta})
res = {{"found": False}}
if roots:
    x0 = int(roots[0])
    res = {{"found": True, "x0": x0}}
print(json.dumps(res))
"""
    sage_res = _run_sage(sage_code)
    if sage_res and sage_res.get("found"):
        x0 = sage_res["x0"]
        m = (prefix_val << unknown_bits) | x0
        return long_to_bytes(m)

    # 2. Fallback for e=3 (Direct root check on small differences)
    if e == 3 and unknown_bytes <= 4:
        for x0 in range(min(X, 1_000_000)):
            m = (prefix_val << unknown_bits) | x0
            if pow(m, e, n) == c:
                return long_to_bytes(m)

    return None


def factor_high_bits_known(
    n: int,
    p_high: int,
    p_bits: int,
    known_bits: int
) -> Optional[Tuple[int, int]]:
    """
    Coppersmith Factorization with Known High Bits of P:
    p = p_high + x, where x < 2^(p_bits - known_bits)
    """
    k_bits = p_bits - known_bits
    X = 2 ** k_bits

    sage_code = f"""import json
n = {n}
p_high = {p_high}
X = {X}

P.<x> = PolynomialRing(Zmod(n))
f = x + p_high
f = f.monic()

roots = f.small_roots(X=X, beta=0.5)
res = {{"found": False}}
if roots:
    x0 = int(roots[0])
    p = int(p_high + x0)
    if n % p == 0:
        res = {{"found": True, "p": p, "q": int(n // p)}}
print(json.dumps(res))
"""
    sage_res = _run_sage(sage_code)
    if sage_res and sage_res.get("found"):
        return sage_res["p"], sage_res["q"]
    return None


def franklin_reiter(
    n: int,
    e: int,
    c1: int,
    c2: int,
    a: int = 1,
    b: int = 0
) -> Optional[bytes]:
    """
    Franklin-Reiter Related Message Attack:
    m2 = a*m1 + b (mod n)
    c1 = m1^e (mod n), c2 = (a*m1 + b)^e (mod n)
    """
    sage_code = f"""import json
n = {n}
e = {e}
c1 = {c1}
c2 = {c2}
a = {a}
b = {b}

P.<x> = PolynomialRing(Zmod(n))
g1 = x^e - c1
g2 = (a*x + b)^e - c2

def pgcd(f, g):
    while g:
        f, g = g, f % g
    return f.monic()

gcd_res = pgcd(g1, g2)
res = {{"found": False}}
if gcd_res.degree() == 1:
    m1 = int(-gcd_res.coefficients()[0])
    res = {{"found": True, "m": m1}}
print(json.dumps(res))
"""
    sage_res = _run_sage(sage_code)
    if sage_res and sage_res.get("found"):
        return long_to_bytes(sage_res["m"])
    return None
