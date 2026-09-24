"""
crypto_toolkit.py - Comprehensive Cryptanalysis & Automated Solver Suite.
"""

import math
from typing import Optional, Tuple, List, Dict, Callable, Any
from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse

ENGLISH_FREQ = {
    'a': 0.08167, 'b': 0.01492, 'c': 0.02782, 'd': 0.04253, 'e': 0.12702,
    'f': 0.02228, 'g': 0.02015, 'h': 0.06094, 'i': 0.06966, 'j': 0.00153,
    'k': 0.00772, 'l': 0.04025, 'm': 0.02406, 'n': 0.06749, 'o': 0.07507,
    'p': 0.01929, 'q': 0.00095, 'r': 0.05987, 's': 0.06327, 't': 0.09056,
    'u': 0.02758, 'v': 0.00978, 'w': 0.02360, 'x': 0.00150, 'y': 0.01974,
    'z': 0.00074, ' ': 0.13000
}


def score_english(data: bytes) -> float:
    score = 0.0
    for b in data:
        char = chr(b).lower()
        if char in ENGLISH_FREQ:
            score += ENGLISH_FREQ[char]
        elif 32 <= b <= 126:
            score += 0.005
        elif b in (9, 10, 13):
            score += 0.001
        else:
            score -= 0.25
    return score / max(1, len(data))


def isqrt(n: int) -> int:
    if n < 0:
        raise ValueError("Square root of negative number")
    if n == 0:
        return 0
    x, y = n, (n + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def iroot(n: int, k: int) -> Tuple[int, bool]:
    """Integer k-th root of n. Returns (root, is_exact)."""
    if n < 0:
        raise ValueError("Negative number")
    if n == 0:
        return 0, True
    if k == 1:
        return n, True
    if k == 2:
        r = isqrt(n)
        return r, (r * r == n)

    # If exponent is excessively large, direct root finding is not small-e
    if k > 1000:
        return 0, False

    # Binary search for exact k-th root
    low = 0
    high = 1
    while high ** k <= n:
        high *= 2
    low = high // 2

    while low <= high:
        mid = (low + high) // 2
        p = mid ** k
        if p == n:
            return mid, True
        elif p < n:
            low = mid + 1
        else:
            high = mid - 1
    return high, False


def rsa_small_e(c: int, e: int = 3) -> Optional[bytes]:
    """Recover plaintext if m^e < N and e is small."""
    if e > 100:
        return None
    r, exact = iroot(c, e)
    if exact:
        try:
            return long_to_bytes(r)
        except Exception:
            return None
    return None


def cube_root_attack(c: int, n: int, e: int = 3, k_max: int = 100_000) -> Optional[bytes]:
    """Solve m^e = c + k*n for small k (picoCTF Mini RSA variant)."""
    for k in range(k_max):
        target = c + k * n
        r, exact = iroot(target, e)
        if exact:
            try:
                res = long_to_bytes(r)
                if score_english(res) > 0.02 or b"{" in res:
                    return res
            except Exception:
                continue
    return None


def fermat_factor(n: int, max_steps: int = 1_000_000) -> Optional[Tuple[int, int]]:
    a = isqrt(n)
    if a * a < n:
        a += 1
    b2 = a * a - n
    step = 0
    while step < max_steps:
        b = isqrt(b2)
        if b * b == b2:
            p = a - b
            q = a + b
            if p * q == n and p > 1 and q > 1:
                return p, q
        a += 1
        b2 = a * a - n
        step += 1
    return None


def continued_fractions(n: int, d: int):
    while d != 0:
        q = n // d
        yield q
        n, d = d, n - d * q


def convergents(cf):
    n_prev, n_curr = 0, 1
    d_prev, d_curr = 1, 0
    for q in cf:
        n_prev, n_curr = n_curr, q * n_curr + n_prev
        d_prev, d_curr = d_curr, q * d_curr + d_prev
        yield n_curr, d_curr


def wiener_attack(n: int, e: int) -> Optional[int]:
    cf = continued_fractions(e, n)
    for k, d in convergents(cf):
        if k == 0 or d % 2 == 0:
            continue
        if (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        s = n - phi + 1
        disc = s * s - 4 * n
        if disc >= 0:
            sq = isqrt(disc)
            if sq * sq == disc and (s + sq) % 2 == 0:
                return d
    return None


def factordb_lookup(n: int) -> Optional[Tuple[int, int]]:
    try:
        import requests
        url = f"http://factordb.com/api?query={n}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") in ("FF", "CF"):
                factors = data.get("factors", [])
                primes = []
                for factor, count in factors:
                    for _ in range(count):
                        primes.append(int(factor))
                if len(primes) >= 2:
                    p = primes[0]
                    q = n // p
                    if p * q == n:
                        return p, q
    except Exception:
        pass
    return None


def solve_rsa(n: int, e: int, c: int) -> Optional[bytes]:
    """
    Automated RSA Decision-Tree Orchestrator:
    1. Direct small-e root (m^e < N)
    2. Small k*n shift scan (Mini RSA)
    3. Wiener's attack (small d)
    4. Fermat factorization (close p, q)
    5. FactorDB API lookup
    """
    # 1. Direct small-e (only if e <= 100)
    if e <= 100:
        pt = rsa_small_e(c, e)
        if pt:
            return pt

    # 2. Mini RSA: small k*N shift
    if e <= 5:
        pt = cube_root_attack(c, n, e, k_max=10_000)
        if pt:
            return pt

    # 3. Wiener's attack
    d = wiener_attack(n, e)
    if d:
        m = pow(c, d, n)
        return long_to_bytes(m)

    # 4. Fermat factorization
    factors = fermat_factor(n, max_steps=50_000)
    if factors:
        p, q = factors
        phi = (p - 1) * (q - 1)
        d = inverse(e, phi)
        return long_to_bytes(pow(c, d, n))

    # 5. FactorDB lookup
    factors = factordb_lookup(n)
    if factors:
        p, q = factors
        phi = (p - 1) * (q - 1)
        d = inverse(e, phi)
        return long_to_bytes(pow(c, d, n))

    return None


def ecdsa_recover_reused_nonce(r: int, s1: int, s2: int, h1: int, h2: int, q: int) -> Optional[int]:
    num_k = (h1 - h2) % q
    den_k = (s1 - s2) % q
    if den_k == 0:
        return None
    k = (num_k * inverse(den_k, q)) % q
    
    num_d = (s1 * k - h1) % q
    d = (num_d * inverse(r, q)) % q
    return d


def pohlig_hellman_dlp(g: int, h: int, p: int, factors: Optional[List[Tuple[int, int]]] = None) -> Optional[int]:
    from sympy.ntheory.residue_ntheory import discrete_log
    try:
        x = discrete_log(p, h, g)
        return int(x)
    except Exception:
        pass
    return None


def meet_in_the_middle(
    pt: bytes,
    ct: bytes,
    encrypt_fn: Callable[[bytes, bytes], bytes],
    decrypt_fn: Callable[[bytes, bytes], bytes],
    candidate_keys: List[bytes]
) -> Optional[Tuple[bytes, bytes]]:
    lookup: Dict[bytes, bytes] = {}
    for k1 in candidate_keys:
        mid = encrypt_fn(k1, pt)
        lookup[mid] = k1

    for k2 in candidate_keys:
        mid = decrypt_fn(k2, ct)
        if mid in lookup:
            return lookup[mid], k2
    return None


def break_single_byte_xor(ciphertext: bytes) -> Tuple[int, bytes, float]:
    best_key = 0
    best_pt = b""
    best_score = -999.0
    for key in range(256):
        pt = bytes([b ^ key for b in ciphertext])
        score = score_english(pt)
        if score > best_score:
            best_score = score
            best_key = key
            best_pt = pt
    return best_key, best_pt, best_score


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = egcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y


def rsa_common_modulus(n: int, e1: int, e2: int, c1: int, c2: int) -> Optional[bytes]:
    gcd, s1, s2 = egcd(e1, e2)
    if gcd != 1:
        return None
    if s1 < 0:
        c1 = pow(c1, -1, n)
        s1 = -s1
    if s2 < 0:
        c2 = pow(c2, -1, n)
        s2 = -s2
    m = (pow(c1, s1, n) * pow(c2, s2, n)) % n
    try:
        return long_to_bytes(m)
    except Exception:
        return None


def hastads_broadcast_attack(moduli: List[int], ciphertexts: List[int], e: int = 3) -> Optional[bytes]:
    if len(moduli) < e or len(ciphertexts) < e:
        return None
    N = 1
    for n in moduli[:e]:
        N *= n
    total = 0
    for n, c in zip(moduli[:e], ciphertexts[:e]):
        N_i = N // n
        gcd, inv, _ = egcd(N_i, n)
        inv %= n
        total = (total + c * N_i * inv) % N
    return rsa_small_e(total, e)


def baby_step_giant_step(g: int, h: int, p: int, max_order: Optional[int] = None) -> Optional[int]:
    m = isqrt(max_order or p) + 1
    table = {}
    cur = 1
    for j in range(m):
        table[cur] = j
        cur = (cur * g) % p
    g_m = pow(g, -m, p)
    gamma = h
    for i in range(m):
        if gamma in table:
            return i * m + table[gamma]
        gamma = (gamma * g_m) % p
    return None
