# Kakashi's Secret Jutsu - Crypto Challenge

## Challenge Description

Kakashi sensei has hidden his secret jutsu behind a cryptographic challenge. Can you use your Sharingan to see through his encryption and recover the hidden secret?

**Difficulty:** Medium  
**Category:** Cryptography  
**Port:** 10000

## Challenge Overview

This is an AES-CBC padding oracle challenge where players must:
1. Complete a proof-of-work challenge
2. Exploit the padding oracle to recover a 48-byte secret
3. Submit the secret to receive the flag

## Deployment

### Using Docker

```bash
docker build -t kakashi-jutsu .
docker run -d -p 10000:10000 --name kakashi-challenge kakashi-jutsu
```

### Connect to Challenge

```bash
nc localhost 10000
```

## Flag Format

```
H7CTF{K4K4SH1_5H4R1NG4N_$33_411_<UUID>}
```

The flag is dynamically generated with a unique UUID for each deployment.

## Technical Details

- **Encryption:** AES-128-CBC
- **Vulnerability:** Padding oracle (custom padding scheme)
- **Secret Size:** 48 bytes (random)
- **IV:** Provided to player
- **Timeout:** 20 minutes per connection

## Challenge Flow

1. Player connects via nc
2. Server displays banner and proof-of-work
3. Player solves PoW (sha256 prefix collision)
4. Server generates random 48-byte secret and 16-byte IV
5. Menu options:
   - Option 1: Encrypt arbitrary message + secret (oracle)
   - Option 2: Submit guess for the secret
   - Option 3: Exit

## Files

- `source.py` - Main challenge server
- `Dockerfile` - Container setup with dynamic flags
- `docker-entrypoint.sh` - Generates UUID and sets FLAG environment variable
- `README.md` - This file

## Solution Approach

Players need to:
1. Understand AES-CBC padding oracle attacks
2. Use the encryption oracle to leak information about the secret
3. Craft specific inputs to extract secret bytes
4. Recover the full 48-byte secret
5. Submit it to get the flag

## Dependencies

- Python 3.10
- pycryptodome
- gmpy2
- uuid-runtime (for dynamic flags)

## Notes

- The server uses `ForkingMixIn` for handling multiple concurrent connections
- Each connection has a 20-minute timeout
- Flag is injected via environment variable at container startup
