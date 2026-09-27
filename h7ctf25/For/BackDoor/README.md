# BackDoor

**Category**: Forensics / Reverse Engineering  
**Difficulty**: Medium  

## Description

While casually browsing the internet, I suddenly received a strange authentication prompt from my browser. I ignored it at first, but a few hours later, I noticed that several important files and personal data had disappeared from my system. I suspect that my computer may have been compromised.

**Your Mission**: Conduct a full forensic investigation to identify what happened, trace the attacker's actions, and answer all the provided questions based on your findings.

## Challenge Files

**Evidence Download**: https://drive.google.com/file/d/1bxIF4afBKLShP1DTk5ENfAK-QwOQuRX-/view  
**Archive Password**: `H7CTF`


**Flag Regex**:
```regex
^H7CTF\{D1sc0rd_1s_p0w3rfull_t0_s1mul@t3_C2_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\}$
```