---
challenge: volteye
category: crypto
techniques: [batch-gcd, rsa-shared-factor, pkcs1-v1.5-unpadding]
time_to_flag: 5
status: solved
---

# VoltEye Camera Cloud — RSA Shared Factor (Batch GCD) Writeup

## 1. Challenge Overview
- **Service:** VoltEye Camera Cloud (`https://web-778e0885961c1427.web.h7tex.com`)
- **Endpoints:**
  - `GET /fleet`: Public key certificates for 30 camera devices
  - `GET /captured`: One intercepted provisioning ciphertext (RSA/PKCS1v1.5) for device serial `VE-CE55D3D6`
  - `POST /admin {"token": "..."}`: Administration unlock endpoint

## 2. Vulnerability & Attack Primitive
- "VoltEye ships a whole fleet of identical cameras, cranked out on the same assembly line... Family resemblance runs deeper than you'd think."
- The PRNG seeding on the manufacturing line lacked sufficient entropy, causing distinct devices to generate RSA moduli sharing prime factors.
- Computing pairwise $\gcd(N_{\text{target}}, N_i)$ across the 30 fleet certificates reveals that device `VE-CE55D3D6` shares a 512-bit prime factor $p$ with device `VE-2E8FCAE2`:
  $$p = \gcd(N_{\text{target}}, N_{\text{VE-2E8FCAE2}}) = 12402147729738018475005121939362487309968660791706956689428404665367497182708558107245952355245113959579691797681384879202879671231050030601736566591322939$$
  $$q = N_{\text{target}} / p$$

## 3. Decryption & Administration Unlock
- Having factored $N$, compute $\phi(N) = (p - 1)(q - 1)$ and private exponent $d = e^{-1} \pmod{\phi(N)}$.
- Decrypt ciphertext $c$: $m = c^d \pmod N$.
- Strip PKCS#1 v1.5 padding (`00 02 [padding] 00 [token]`) to recover the admin bootstrap token:
  `vlt_7f99dac571e46c48085f5049`
- Submit to `POST /admin`:
  ```json
  {"authed": true, "flag": "H7CTF{a1589059-de3a-4b5a-995f-c06675a0559d}"}
  ```

## 4. Recovered Flag
```text
H7CTF{a1589059-de3a-4b5a-995f-c06675a0559d}
```
