---
challenge: meridian_logs
category: forensics
techniques: [log_analysis, checkpoint_mapping]
time_to_flag: 5
status: solved
---

# Meridian-7 Log Reassembly

The challenge involves three recovered log files (log1.txt, log2.txt deleted, log3.txt).
Embedded within the daemon noise are two-digit numbered checkpoints:
- 53_IN-USE_log1.txt: 01 to 06
- 54_DELETED_log2.txt: 07 to 13
- 55_IN-USE_log3.txt: 20 to 23

Reassembling the checkpoint map reveals the break between 13 and 20 (checkpoints 14-19 missing).
Reconstructed checkpoint map: 01-06_07-13_20-23
Flag: COE-CS{01-06_07-13_20-23}
