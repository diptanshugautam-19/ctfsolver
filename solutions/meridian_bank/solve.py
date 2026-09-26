import hashlib, zlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

fpath = r'D:\ctf_sifi\all_extracted\48_IN-USE_Bankdetails.gpg'
with open(fpath, 'rb') as f:
    data = f.read()

# Packet 1 (Tag 3): Symmetric-Key Encrypted Session Key Packet (AES-256, Iterated & Salted S2K)
salt = data[6:14]
count_byte = data[14]
count = (16 + (count_byte & 15)) << ((count_byte >> 4) + 6)

# Key derivation from Challenge 4 key: 'thunderbolt'
pw = b'thunderbolt'
data_s2k = salt + pw
key = b''
c_idx = 0
while len(key) < 32:
    h = hashlib.sha1()
    if c_idx > 0:
        h.update(b'\x00' * c_idx)
    chunk = data_s2k * (65536 // len(data_s2k))
    for _ in range(count // len(chunk)):
        h.update(chunk)
    h.update(data_s2k * ((count % len(chunk)) // len(data_s2k)))
    h.update(data_s2k[:count % len(data_s2k)])
    key += h.digest()
    c_idx += 1
key = key[:32]

# Packet 2 (Tag 18): SEIPD decrypted with AES-256 CFB mode (all-zero IV)
ciphertext = data[19:]
cipher = Cipher(algorithms.AES(key), modes.CFB(b'\x00' * 16), backend=default_backend())
decryptor = cipher.decryptor()
pt = decryptor.update(ciphertext) + decryptor.finalize()

# Decompress ZIP / Deflate compressed packet
decomp = zlib.decompress(pt[18:-22][2:], -15)

# Parse Literal Data Packet (Tag 11)
text = decomp[23:].decode('latin1')
lines = {line.split(': ')[0]: line.split(': ')[1] for line in text.split('\r\n') if ': ' in line}

beneficiary = lines['Beneficiary']
routing_code = lines['Routing Code']
flag = f'COE-CS{{{beneficiary}_{routing_code}}}'
print(f'Flag: {flag}')
