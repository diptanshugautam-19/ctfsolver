"""
test_suite.py - Unit test and regression harness for CTF toolkit components.
"""

import unittest
import base64
import math
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes, inverse

from tools.crypto_toolkit import (
    rsa_small_e,
    cube_root_attack,
    fermat_factor,
    wiener_attack,
    solve_rsa,
    ecdsa_recover_reused_nonce,
    meet_in_the_middle,
    break_single_byte_xor,
    rsa_common_modulus,
    baby_step_giant_step,
    isqrt
)
from tools.flag_hunter import FlagHunter
from tools.scope_guard import is_target_allowed, validate_target, ScopeViolationError
from tools.web_toolkit import decode_jwt, forge_jwt_alg_none
from tools.lattice.coppersmith import lll_reduction, small_roots_stereotyped


class TestScopeGuard(unittest.TestCase):
    def test_scope_allowed(self):
        self.assertTrue(is_target_allowed("127.0.0.1", 8000))
        self.assertTrue(is_target_allowed("localhost", 1337))

    def test_scope_blocked(self):
        self.assertFalse(is_target_allowed("192.168.1.50", 22))
        self.assertFalse(is_target_allowed("evil.example.com", 80))
        with self.assertRaises(ScopeViolationError):
            validate_target("evil.example.com", 80)


class TestCryptoPhaseA(unittest.TestCase):
    def test_solve_rsa_small_e(self):
        message = b"flag{small_e_direct}"
        m = bytes_to_long(message)
        e = 3
        p = getPrime(256)
        q = getPrime(256)
        n = p * q
        c = pow(m, e)
        rec = solve_rsa(n, e, c)
        self.assertEqual(rec, message)

    def test_solve_rsa_mini_shifted(self):
        message = b"flag{mini_k3}"
        m = bytes_to_long(message)
        e = 3
        n = 1000000007 * 1000000009
        k_actual = 5
        c = (m**e) - k_actual * n
        rec = cube_root_attack(c, n, e=3, k_max=100)
        self.assertEqual(rec, message)

    def test_solve_rsa_wiener(self):
        p = getPrime(256)
        q = getPrime(256)
        n = p * q
        phi = (p - 1) * (q - 1)
        bound = int((1.0 / 3.0) * (n ** 0.25))
        d = bound // 2
        if d % 2 == 0:
            d += 1
        while math.gcd(d, phi) != 1:
            d += 2
        e = pow(d, -1, phi)
        message = b"flag{wiener_orchestrated}"
        c = pow(bytes_to_long(message), e, n)
        rec = solve_rsa(n, e, c)
        self.assertEqual(rec, message)

    def test_ecdsa_nonce_reuse(self):
        q = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        d = 0x1337BEEFCAFE
        k = 0x9876543210ABCDEF
        r = 0x424242424242

        h1 = 0xAAAA111122223333
        h2 = 0xBBBB444455556666

        s1 = (inverse(k, q) * (h1 + d * r)) % q
        s2 = (inverse(k, q) * (h2 + d * r)) % q

        rec_d = ecdsa_recover_reused_nonce(r, s1, s2, h1, h2, q)
        self.assertEqual(rec_d, d)

    def test_meet_in_the_middle(self):
        def enc(k: bytes, data: bytes) -> bytes:
            return bytes([((b ^ k[0]) * 3 + 7) % 256 for b in data])

        def dec(k: bytes, data: bytes) -> bytes:
            inv3 = 171
            return bytes([(((b - 7) * inv3) % 256) ^ k[0] for b in data])

        k1 = bytes([42])
        k2 = bytes([123])
        pt = b"flag{meet_in_middle_confirmed_12345}"
        ct = enc(k2, enc(k1, pt))

        candidates = [bytes([i]) for i in range(256)]
        rec_k1, rec_k2 = meet_in_the_middle(pt, ct, enc, dec, candidates)
        self.assertEqual(rec_k1, k1)
        self.assertEqual(rec_k2, k2)

    def test_single_byte_xor(self):
        msg = b"CTF{x0r_is_e4sy_when_scored_with_english_freq}"
        key = 0x5A
        ct = bytes([b ^ key for b in msg])
        rec_key, rec_pt, score = break_single_byte_xor(ct)
        self.assertEqual(rec_key, key)
        self.assertEqual(rec_pt, msg)

    def test_rsa_common_modulus(self):
        p = getPrime(256)
        q = getPrime(256)
        n = p * q
        phi = (p - 1) * (q - 1)
        msg = b"flag{common_modulus_solved}"
        m = bytes_to_long(msg)
        e1 = 3
        e2 = 5
        c1 = pow(m, e1, n)
        c2 = pow(m, e2, n)
        rec = rsa_common_modulus(n, e1, e2, c1, c2)
        self.assertEqual(rec, msg)


class TestWebToolkit(unittest.TestCase):
    def test_jwt_alg_none_forgery(self):
        original_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ3Vlc3QiLCJhZG1pbiI6ZmFsc2V9.abc"
        h, p, _ = decode_jwt(original_token)
        p["admin"] = True
        p["user"] = "admin"
        forged = forge_jwt_alg_none(h, p)
        h_mod, p_mod, _ = decode_jwt(forged)
        self.assertEqual(h_mod["alg"], "none")
        self.assertEqual(p_mod["user"], "admin")
        self.assertTrue(p_mod["admin"])


class TestFlagHunter(unittest.TestCase):
    def test_auto_accept_direct(self):
        data = b"Some random garbage text flag{test_auto_accept_1234} more garbage"
        hunter = FlagHunter()
        hunter.hunt(data)
        flags = [c.flag for c in hunter.auto_accepts]
        self.assertIn("flag{test_auto_accept_1234}", flags)

    def test_recursive_base64(self):
        inner = b"picoCTF{r3cursiv3_b4se64_d3t3ct3d}"
        layer1 = base64.b64encode(inner)
        layer2 = base64.b64encode(layer1)
        container = b"The secret payload is: " + layer2
        hunter = FlagHunter(max_depth=5)
        hunter.hunt(container)
        flags = [c.flag for c in hunter.auto_accepts]
        self.assertIn("picoCTF{r3cursiv3_b4se64_d3t3ct3d}", flags)


class TestLatticePhaseB(unittest.TestCase):
    def test_lll_reduction(self):
        basis = [
            [1, 1, 1],
            [-1, 0, 2],
            [3, 5, 6]
        ]
        red = lll_reduction(basis)
        self.assertEqual(len(red), 3)
        self.assertEqual(red[0], [0, 1, 0])


if __name__ == "__main__":
    unittest.main()
