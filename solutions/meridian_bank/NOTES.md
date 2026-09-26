---
challenge: meridian_bank
category: forensics
techniques: [openpgp_analysis, aes_cfb_decryption, s2k_derivation, zlib_decompression]
time_to_flag: 10
status: solved
---

# Meridian-7 Bankdetails.gpg Decryption

1. Packet Analysis of Bankdetails.gpg:
   - Tag 3: SKESK packet specifies AES-256 (cipher ID 9), SHA-1 (hash ID 2), Iterated & Salted S2K (type 3).
   - Tag 18: SEIPD packet (AES-256 CFB mode with all-zero IV, no resync).
2. Key Derivation:
   - Passphrase 	hunderbolt from Challenge 4 with salt 3b93d9b649eb2920 and count 65011712.
3. Decryption & Decompression:
   - SEIPD decrypted using AES-256-CFB.
   - Inner packet is Compressed Data Packet (Tag 8, Deflate algorithm).
   - Plaintext Literal Data Packet (Tag 11) yields Bankdetails.txt:
     - Bank Name: Midland Overseas Trust
     - Account: #03994822-INT
     - Routing Code: 4827-WGHL-002
     - Beneficiary: R. Specter
4. Flag:
   COE-CS{R. Specter_4827-WGHL-002}
