# KGF 2.0

## Hard-Tier Forensics Challenge (2950 pts)

**Difficulty:** Hard  
**Category:** Forensics / Advanced Malware Analysis  
**Points:** 2950 (8 questions × 200-500 pts each)

---

## Challenge Description

This is the advanced continuation of **KGF 1.0**. Having uncovered the surface-level infrastructure, you must now dive deeper into the malware's cryptographic operations, mining pool configurations, and compilation artifacts.

These challenges require advanced binary analysis skills including UPX unpacking, base64 decoding, Go module forensics, and multi-stage data extraction.

**Prerequisites:** Complete KGF 1.0 before attempting this challenge!

---

## Objectives

Answer all 8 advanced questions correctly by performing deep binary analysis on the compromised container to receive the flag.

**Questions cover:**
- MD5 integrity verification
- UPX binary unpacking
- Mining pool FQDN extraction
- Cryptocurrency wallet forensics
- Base64-encoded alternate configurations
- Mining protocol identification
- Go compilation timestamp analysis

---

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- UPX (Ultimate Packer for eXecutables)
- Advanced forensics skills
- Completion of KGF 1.0

### Install UPX

```bash
# Debian/Ubuntu
sudo apt-get install upx-ucl

# macOS
brew install upx

# Or download from: https://upx.github.io/
```

### Use Same Container Snapshot

You'll use the same `compromised.tar` from KGF 1.0:
```bash
# If you haven't extracted it yet
tar -xf compromised.tar -C container_fs
cd container_fs
```

### Start the Challenge

```bash
# Build and run
docker-compose up -d

# Or using docker directly
docker build -t kgf-part2 .
docker run -p 3001:3000 kgf-part2
```

Access the challenge at: `http://localhost:3001`

---

## Advanced Analysis Techniques

### UPX Unpacking
```bash
# Unpack the kdevtmpfsi miner
upx -d tmp/kdevtmpfsi -o tmp/kdevtmpfsi_unpacked

# Verify unpacking
file tmp/kdevtmpfsi_unpacked
```

### Base64 Decoding
```bash
# Find base64-encoded strings
strings tmp/kdevtmpfsi_unpacked | grep -E "^[A-Za-z0-9+/]{40,}=$"

# Decode specific string
echo "BASE64_STRING_HERE" | base64 -d
```

### Go Module Analysis
```bash
# Extract Go dependencies
strings etc/kinsing | grep "golang.org"

# Find version timestamps
strings etc/kinsing | grep "v0.0.0-"
```

### Mining Pool Discovery
```bash
# Search for pool domains
strings tmp/kdevtmpfsi_unpacked | grep -i "pool\|nanopool\|monero"

# Find stratum connections
strings tmp/kdevtmpfsi_unpacked | grep -i "stratum"
```

### Wallet Address Extraction
```bash
# Monero addresses are 95 chars starting with '4'
strings tmp/kdevtmpfsi_unpacked | grep -E "^4[0-9A-Za-z]{94}$"

# Search in base64 encoded data
strings tmp/kdevtmpfsi_unpacked | grep -E "^[A-Za-z0-9+/]{100,}=$" | while read line; do
  echo "$line" | base64 -d 2>/dev/null | grep -E "^4[0-9A-Za-z]{94}$"
done
```

---

## Advanced Learning Outcomes

By completing this challenge, you will master:
- Binary unpacking and anti-analysis evasion
- Multi-stage data extraction techniques
- Cryptocurrency infrastructure forensics
- Go binary compilation artifacts
- Base64 obfuscation techniques
- Mining pool protocol analysis
- Dependency timestamp forensics

---

## Flag Format

```
H7CTF{w3ll_w3ll_w3ll_s0meone_h4s_4_g00dy_2_eyes_<uuid>}
```

The flag is dynamically generated for each challenge instance.

---

## Challenge Hints

### Question-Specific Tips

**Q9 (MD5 Hash):** Look in the embedded shell script for integrity checks  
**Q10 (Distribution):** Check what grep command looks for in /etc/os-release  
**Q11 (Mining Pool):** Unpack first, then search for "nanopool"  
**Q12 (Primary Wallet):** 95 characters, starts with '46V5'  
**Q13 (Backup Pools):** Count domain-based pools (NOT IP addresses)  
**Q14 (Protocol):** Used for cryptocurrency mining, think "layers"  
**Q15 (Alternative Wallet):** Base64-encoded, starts with '44Mt'  
**Q16 (Compilation Date):** Go module version format reveals timestamp  

---

## Scoring

| Question | Points | Topic |
|----------|--------|-------|
| 9 | 350 | Scanner MD5 Integrity |
| 10 | 250 | Linux Distribution Detection |
| 11 | 400 | Primary Mining Pool FQDN |
| 12 | 500 | Primary Wallet Address |
| 13 | 300 | Backup Pool Infrastructure |
| 14 | 200 | Mining Protocol |
| 15 | 450 | Alternative Wallet (Base64) |
| 16 | 500 | Compilation Timestamp |
| **Total** | **2950** | |

---

## Advanced Rules

1. **UPX unpacking is REQUIRED** for most questions
2. Some answers are encoded in base64 - decode first!
3. Pay strict attention to answer formats (case-sensitivity varies)
4. Character count hints are your friend
5. All answers must be correct simultaneously to get the flag

---

## Series Completion

Congratulations! You've completed the KGF Challenge Series:
- Part 1: KGF 1.0 (Mid-Tier)
- Part 2: KGF 2.0 (Hard-Tier - You are here)

**Total Points if both completed:** 4,550 points

---

## Troubleshooting

### UPX Unpacking Issues
```bash
# If UPX fails
upx -d --force tmp/kdevtmpfsi -o tmp/kdevtmpfsi_unpacked

# Verify unpacking success
strings tmp/kdevtmpfsi_unpacked | grep "coin"
```

### Base64 Decoding Issues
```bash
# Remove whitespace and newlines
echo "STRING" | tr -d '\n' | base64 -d
```

### Wrong Answer Lengths
- Double-check character count hints
- Ensure no leading/trailing spaces
- Verify case sensitivity requirements

---

## Author

**Challenge by:** AbuCTF Team  
**Category:** Forensics (Advanced)  
**Difficulty:** Hard  
**Recommended Time:** 3-4 hours

---

## Support

If you encounter technical issues:
- Ensure UPX is properly installed
- Check Docker logs: `docker logs [container_id]`
- Verify container filesystem is accessible
- Port 3000 must be available

For challenge-related questions, consult the CTF platform's support channel.
