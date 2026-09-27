# Challenge 3: Vault Heist - Missing Signer Check

## Challenge Overview
**Difficulty:** Medium  
**Category:** Solana Smart Contract Security  
**Vulnerability:** Missing Signer Check in Authorization

## Description
A vault program holds 50 SOL in a PDA. The vault has an admin who can withdraw funds. Players start with 5 SOL and must steal at least 40 SOL to capture the flag.

## Vulnerability
The `AdminWithdraw` instruction checks if the provided account matches the admin's public key but **fails to verify that the account is actually a signer**. This allows anyone to call the admin withdraw function by simply providing the admin's public key as a parameter.

**Vulnerable Code Location:** `program/src/processor.rs` in `process_admin_withdraw()`
```rust
// Checks admin pubkey matches, but NOT if admin is a signer!
if vault_data.admin != *admin_account.key {
    msg!("Only admin can withdraw from vault");
    return Err(ProgramError::InvalidAccountData);
}
```

## Directory Structure

```
challenge-3-vault-heist/
├── challenge/          # Production deployment
│   ├── Dockerfile
│   ├── entrypoint.sh  # Generates dynamic flag
│   ├── program/       # Symlinked to ../program
│   └── server/        # Symlinked to ../server
│
├── dist/              # Player distribution (give to players)
│   ├── Dockerfile
│   ├── program/       # Cleaned source (no vuln comments)
│   ├── server/        # Challenge server
│   └── solve/         # Empty template for solution
│
├── program/           # Vulnerable smart contract source
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       ├── processor.rs   # Contains vulnerability
│       └── entrypoint.rs
│
├── server/            # CTF framework server
│   ├── Cargo.toml
│   └── src/
│       └── main.rs    # Challenge setup & validation
│
└── solve/             # Reference solution (DO NOT DISTRIBUTE)
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        └── processor.rs   # Working exploit
```

## Deployment

### Using Docker (Recommended)
```bash
cd challenge/
docker build -t vault-heist .
docker run -p 5003:5003 vault-heist
```

The entrypoint script automatically generates a dynamic flag with UUID.

### Manual Build
```bash
# Build program
cd program
cargo build-sbf

# Build server
cd ../server
cargo build --release

# Run server
cd ..
./server/target/release/vault-heist-server
```

## Configuration
- **Port:** 5003
- **Starting Balance:** 5 SOL
- **Vault Balance:** 50 SOL  
- **Win Threshold:** 40 SOL (player must have ≥40 SOL)
- **Flag Format:** `H7CTF{m1ss1ng_s1gn3r_ch3ck_1s_4_cl4ss1c_vuln_<UUID>}`

## Player Distribution

Create the player package:
```bash
cd dist/
tar -czf vault-heist-player.tar.gz Dockerfile program/ server/ solve/
```

Give players `vault-heist-player.tar.gz` containing:
- Full source code (cleaned, no vulnerability hints)
- Server binary setup
- Empty solve template
- Dockerfile for local testing

## Solution Approach

1. **Analyze the program** - Players should audit `program/src/processor.rs`
2. **Identify the vulnerability** - Missing `is_signer` check in `AdminWithdraw`
3. **Craft exploit** - Create CPI to vault program's `AdminWithdraw` with:
   - Vault PDA (writable)
   - Admin pubkey (NOT as signer, just read-only account)
   - Player account (recipient)
4. **Build and test**:
   ```bash
   cd solve
   cargo build-sbf
   python3 ../solve.py
   ```

## Testing Locally

Players can test against the dist version:
```bash
cd dist/
docker build -t vault-heist-local .
docker run -p 5002:5002 vault-heist-local
```

Then run solve script against `localhost:5002`.

## Security Notes

- The vulnerability is realistic - missing signer checks are a common Solana security issue
- This demonstrates the importance of validating **both** identity AND authorization
- Fix: Add `if !admin_account.is_signer` check before allowing withdrawal

## Framework

Built using [sol-ctf-framework](https://github.com/otter-sec/sol-ctf-framework) by Ottersec.

## Admin Commands

Check if running:
```bash
nc localhost 5003
```

Monitor logs:
```bash
docker logs -f <container-id>
```
