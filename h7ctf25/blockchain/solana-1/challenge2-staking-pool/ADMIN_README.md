# Challenge 2: Staking Pool - ADMIN README

## Challenge Overview
**Difficulty:** Hard  
**Category:** Solana Smart Contract Security  
**Vulnerability:** PDA Seed Collision / Insufficient Seed Separation

## Quick Reference
- **Port:** 5001
- **Starting Balance:** 10 SOL
- **Admin Pool Balance:** 100 SOL
- **Win Threshold:** 50 SOL
- **Vuln Type:** PDA seed collision (string concatenation)

## Directory Structure

```
challenge2-staking-pool/
├── deploy/            # Production deployment
│   ├── Dockerfile
│   ├── entrypoint.sh  # Dynamic flag generation
│   ├── program/       # Symlinked to ../program
│   └── server/        # Symlinked to ../server
│
├── dist/              # Player distribution
│   ├── Dockerfile
│   ├── program/       # Cleaned source
│   ├── server/        # Challenge server
│   └── solve/         # Template only
│
├── program/           # Vulnerable smart contract
├── server/            # CTF framework server
├── solve/             # Reference solution (SECRET)
└── README.md          # Player-facing instructions
```

## Deployment

### Production (with dynamic flags)
```bash
cd deploy/
docker build -t h7ctf-staking-pool .
docker run -d -p 5001:5001 --name staking-pool h7ctf-staking-pool
```

### Test Locally
```bash
cd dist/
docker build -t staking-pool-test .
docker run -p 5001:5001 staking-pool-test
```

## Vulnerability Explanation

The program derives PDAs using concatenated strings:
```rust
&[b"POOL", organization.as_bytes(), employee_id.as_bytes()]
```

**Collision:**
- Admin: `"H7Corp" + "admin"` → bytes: `H7Corpadmin`
- Attack: `"H7Cor" + "padmin"` → bytes: `H7Corpadmin`

Same PDA = unauthorized access to admin pool!

## Solution Overview

1. Recognize PDA seed concatenation issue
2. Find collision: `"H7Cor" + "padmin"` = `"H7Corp" + "admin"`
3. Call Withdraw instruction with colliding seeds
4. Steal 50+ SOL from admin pool

## Player Distribution

Give players the `dist/` folder:
```bash
cd dist/
tar -czf staking-pool-player.tar.gz *
```

This includes:
- Cleaned program source (no vulnerability comments)
- Server for local testing
- Empty solve template
- Dockerfile

## Monitoring

Check logs:
```bash
docker logs -f staking-pool
```

Connect manually:
```bash
nc localhost 5001
```

## Testing Solution

```bash
cd solve/
cargo build-sbf
cd ..
python3 solve.py localhost 5001
```

Expected output should show:
- Initial balance: 10 SOL
- Final balance: 60 SOL (50 stolen + 10 starting)
- Flag captured

## Flag Format
```
H7CTF{pda_s33d_c0ll1s10n_unlocks_admin_p00l_<UUID>}
```

Generated dynamically by entrypoint.sh using `uuidgen`.

## Common Issues

**Players can't find collision:**
- Hint them about string concatenation
- Ask: what produces same bytes?

**Docker build fails:**
- Ensure Solana toolchain installs correctly
- Check cargo-build-sbf vs cargo build-sbf

**Port already in use:**
- Change port mapping: `-p 5002:5001`
- Update SERVER_PORT in server/src/main.rs

## Security Notes

This is a REAL vulnerability class:
- Found in Saber Protocol (2021)
- Found in Mercurial Finance (2021)  
- Demonstrates importance of seed design

Proper fix requires:
- Length-prefixed seeds
- Delimiter bytes between variable fields
- Or hash variable-length inputs

## Framework

Uses [sol-ctf-framework](https://github.com/otter-sec/sol-ctf-framework) by Ottersec.
