---
challenge: trace_amounts
category: hardware
techniques: [side_channel_analysis, correlation_power_analysis, aes128_cpa, hamming_weight_leakage]
time_to_flag: 5
status: solved
---

# Trace Amounts (Smart-Card Power Capture) — Writeup

## 1. Challenge Overview
- **Instance URL:** `https://web-34ab308fe4c8fd21.web.h7tex.com`
- **Artifacts:**
  - `traces.npy`: float32 array, $500 \times 700$ (power trace per authorization).
  - `plaintexts.npy`: uint8 array, $500 \times 16$ (known challenge plaintexts).
  - `secret.enc`: 48 bytes encrypted with card's AES-128 key in ECB mode.
- **Description:** A contactless payment card executes AES-128 to authorize taps. A current probe logged 500 authorizations. Recover the key and decrypt `secret.enc`.

## 2. Power Model & Side-Channel Leakage
1. **Target Operation:**
   - In AES-128 Round 1, the plaintext $P$ is XORed with Round Key $K$, followed by SubBytes:
     $$Y_{i} = \text{SBox}(P_i \oplus K_i) \quad \text{for } i \in \{0, 1, \dots, 15\}$$
2. **Leakage Model:**
   - Standard CMOS logic registers and bus lines dissipate dynamic power proportional to the number of switching bits (Hamming Distance) or number of 1-bits loaded onto an internal pre-charged bus (Hamming Weight):
     $$H(P_i, K_i) = \text{HW}(\text{SBox}(P_i \oplus K_i))$$
3. **Correlation Power Analysis (CPA):**
   - For each byte index $i \in \{0, \dots, 15\}$ and key hypothesis $k \in \{0, \dots, 255\}$, compute Pearson's correlation coefficient $\rho(k, t)$ across $N = 500$ traces and time samples $t \in [0, 699]$:
     $$\rho(k, t) = \frac{\sum_{n=1}^{N} (H_{n, k} - \bar{H}_k)(T_{n, t} - \bar{T}_t)}{\sqrt{\sum_{n=1}^{N} (H_{n, k} - \bar{H}_k)^2 \sum_{n=1}^{N} (T_{n, t} - \bar{T}_t)^2}}$$
   - The correct key byte produces a sharp correlation peak ($|\rho| \approx 0.65 - 0.73$), while incorrect hypotheses remain at noise level ($|\rho| \approx 0.18 - 0.20$).

## 3. Results & Key Recovery
- Peak sample index exhibits an exact stride of $40$ samples per S-box lookup:
  - Byte 0: `0x39`, $\rho = 0.6614$ at sample 30
  - Byte 1: `0x0e`, $\rho = 0.6920$ at sample 70
  - Byte 2: `0x95`, $\rho = 0.6876$ at sample 110
  - Byte 3: `0x8b`, $\rho = 0.6625$ at sample 150
  - Byte 4: `0x16`, $\rho = 0.7270$ at sample 190
  - Byte 5: `0xed`, $\rho = 0.6764$ at sample 230
  - Byte 6: `0x6d`, $\rho = 0.6993$ at sample 270
  - Byte 7: `0x80`, $\rho = 0.6992$ at sample 310
  - Byte 8: `0x1d`, $\rho = 0.6737$ at sample 350
  - Byte 9: `0xe7`, $\rho = 0.6978$ at sample 390
  - Byte 10: `0x2b`, $\rho = 0.7242$ at sample 430
  - Byte 11: `0x16`, $\rho = 0.6981$ at sample 470
  - Byte 12: `0x2a`, $\rho = 0.6842$ at sample 510
  - Byte 13: `0xaa`, $\rho = 0.6971$ at sample 550
  - Byte 14: `0xc5`, $\rho = 0.7064$ at sample 590
  - Byte 15: `0x88`, $\rho = 0.6571$ at sample 630

- **Recovered AES-128 Key:**
  `390e958b16ed6d801de72b162aaac588`

## 4. Decryption
- Decrypting `secret.enc` with AES-128-ECB and unpadding PKCS#7:
  - Raw Decrypted: `b'H7CTF{975aa919-00a3-4480-8ed0-5acefa944658}\x05\x05\x05\x05\x05'`

## 5. Recovered Flag
`H7CTF{975aa919-00a3-4480-8ed0-5acefa944658}`
