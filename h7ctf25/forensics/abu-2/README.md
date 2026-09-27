# KGF: Part 1 - Kings of Gold Fields

## Mid-Tier Forensics Challenge (1600 pts)

**Difficulty:** Medium  
**Category:** Forensics / Malware Analysis  
**Points:** 1600 (8 questions × 100-400 pts each)

---

## 📖 Challenge Description

A compromised Ubuntu container has been recovered from a cryptomining incident. Your mission is to analyze the container filesystem and uncover the malware's command-and-control infrastructure, persistence mechanisms, and cryptocurrency mining operations.

This is Part 1 of the KGF series, focusing on foundational forensics skills including file system analysis, timestamp investigation, and binary reconnaissance.

---

## Objectives

Answer all 8 questions correctly by analyzing the compromised container to receive the flag.

**Questions cover:**
- C2 server identification
- Persistence timeline analysis
- Cryptocurrency detection
- Binary deployment tracking
- Network infrastructure mapping
- Browser impersonation techniques

---

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Basic Linux command-line knowledge
- Forensics tools (strings, stat, grep, etc.)

### Download Challenge Files

1. **Download the compromised container** (not included in Docker image):
   ```bash
   # Download from challenge server
   wget https://[CHALLENGE_SERVER]/compromised.tar
   # OR
   # Use the provided download link from CTF platform
   ```

2. **Extract the container filesystem**:
   ```bash
   mkdir container_fs
   tar -xf compromised.tar -C container_fs
   cd container_fs
   ```

### Start the Challenge

```bash
# Build and run the challenge
docker-compose up -d

# Or using docker directly
docker build -t kgf-part1 .
docker run -p 3000:3000 kgf-part1
```

Access the challenge at: `http://localhost:3000`

---

## 🔍 Analysis Tips

### Essential Commands
```bash
# View file contents
cat [file_path]

# Extract strings from binaries
strings [binary_path]

# Check file timestamps
stat [file_path]

# Search for patterns
grep -r "pattern" .

# Find files by criteria
find . -name "*.sh" -type f
```

### Key Areas to Investigate
- `/etc/` - System configuration and potential malware
- `/tmp/` - Temporary files and downloaded payloads
- `/var/spool/cron/` - Scheduled tasks (persistence)
- Binary files - Use `strings` command for analysis

---

## Learning Outcomes

By completing this challenge, you will learn:
- Container forensics fundamentals
- Malware persistence mechanisms
- Cryptocurrency mining infrastructure
- Timestamp-based attack timeline reconstruction
- Binary analysis techniques
- Command-and-control (C2) identification

---

## Flag Format

```
H7CTF{n0w_y0u_und3rst4nd_where_th3_n4me_0f_th3_ch4llenge_c0mes_fr0m_<uuid>}
```

The flag is dynamically generated for each challenge instance.

---

## Hint System

Each question includes:
- Expected answer format
- Character count indicator (gray text)
- Real-time validation feedback
- Visual indicators for correct/incorrect answers

---

## Scoring

| Question | Points | Topic |
|----------|--------|-------|
| 1 | 100 | C2 Server IP |
| 2 | 150 | Malicious Script URL |
| 3 | 250 | Backup C2 Infrastructure |
| 4 | 300 | Cron Job Installation Time |
| 5 | 150 | Cryptocurrency Identification |
| 6 | 400 | Binary Deployment Timeline |
| 7 | 250 | User-Agent Fingerprinting |
| 8 | 300 | Network Scanner Detection |
| **Total** | **1600** | |

---

---

## Important Rules

1. All answers must be submitted simultaneously
2. Follow the specified answer format for each question
3. Pay attention to case sensitivity where indicated
4. Use the character count hints to validate answer length
5. Flag is revealed only after all questions are correct

---

## Series Information

This is Part 1 of the KGF challenge series:
- Part 1: KGF 1.0 (Mid-Tier - You are here)
- Part 2: KGF 2.0 (Hard-Tier - Coming next)

Complete Part 1 before attempting Part 2!

---

## Author

**Challenge by:** AbuCTF Team  
**Category:** Forensics  
**Difficulty:** Medium  
**Recommended Time:** 2-3 hours

---

## Support

If you encounter technical issues:
- Check Docker logs: `docker logs [container_id]`
- Ensure port 3000 is not in use
- Verify compromised_ubuntu.tar is properly extracted

For challenge-related questions, consult the CTF platform's support channel.

---

**Good luck, and may the forensics be with you! 🔍**
