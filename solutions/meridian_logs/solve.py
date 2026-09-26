import os
import re

files = [
    r'D:\ctf_sifi\all_extracted\53_IN-USE_log1.txt',
    r'D:\ctf_sifi\all_extracted\54_DELETED_log2.txt',
    r'D:\ctf_sifi\all_extracted\55_IN-USE_log3.txt'
]

ranges = []
for fpath in files:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        checkpoints = [line.strip() for line in f if line.strip().isdigit()]
    if checkpoints:
        ranges.append((int(checkpoints[0]), f'{checkpoints[0]}-{checkpoints[-1]}'))

ranges.sort(key=lambda x: x[0])
flag_body = '_'.join(r[1] for r in ranges)
flag = f'COE-CS{{{flag_body}}}'
print(f'Flag: {flag}')
