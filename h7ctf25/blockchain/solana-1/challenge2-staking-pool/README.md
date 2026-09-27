# Challenge 2: Staking Pool - PDA Seed Collision

## 🎯 Challenge Overview

**Difficulty:** Medium  
**Category:** Solana Smart Contract Security  
**Points:** 500

You've discovered H7Corp's employee staking pool program. The admin pool contains 100 SOL, but only employees with admin privileges should be able to access it. Can you find a way to steal the funds?

## 📋 Challenge Description

H7Corp uses a Solana program to manage employee staking pools. Each employee can create a pool identified by their organization name and employee ID. The admin pool (`H7Corp/admin`) holds 100 SOL in staked funds.

Your goal: **Steal at least 50 SOL from the admin pool!**

## 🔍 Vulnerability

This challenge demonstrates a **PDA Seed Collision vulnerability**. The program derives Program Derived Addresses (PDAs) using concatenated seeds without proper delimiters:

```rust
// Vulnerable PDA derivation
let (pda, bump) = Pubkey::find_program_address(
    &[
        b"POOL",
        organization.as_bytes(),  // "H7Corp" = [72, 55, 67, 111, 114, 112]
        employee_id.as_bytes(),   // "admin" = [97, 100, 109, 105, 110]
    ],
    program_id,
);
```

**The Problem:** 
- `"H7Corp" + "admin"` produces the same byte sequence as `"H7Cor" + "padmin"`!
- Both concatenate to: `[..., 72, 55, 67, 111, 114, 112, 97, 100, 109, 105, 110]`
- This allows unauthorized access to the admin pool!

## 🚀 Getting Started

### Connect to the Challenge

```bash
nc ctf.h7ctf.com 5001
```

You'll receive:
- Your private key (full control)
- Your public key (wallet address)
- Program ID (vulnerable staking program)
- Admin Pool PDA (target with 100 SOL)
- RPC URL (for direct interaction)

### Build Your Exploit

```bash
cd solve
cargo build-sbf
cd ..
python3 solve.py localhost 5001
```

## 💡 Hints

<details>
<summary>Hint 1: Understanding PDAs</summary>

PDAs are derived deterministically from seeds. The same seeds ALWAYS produce the same PDA. Look at how the seeds are concatenated!

</details>

<details>
<summary>Hint 2: Seed Collision</summary>

Think about string concatenation:
- `"ABC" + "DEF"` = `"ABCDEF"`
- `"ABCD" + "EF"` = `"ABCDEF"`

Can you apply this to `"MegaCorp"` and `"admin"`?

</details>

<details>
<summary>Hint 3: The Exploit</summary>

Create a pool with:
- Organization: `"MegaCor"` (missing the 'p')
- Employee ID: `"padmin"` (starts with 'p')

This will derive the SAME PDA as the admin pool, giving you access to withdraw!

</details>

## 🎓 Learning Objectives

After completing this challenge, you'll understand:

1. **PDA Derivation**: How Solana derives addresses from seeds
2. **Seed Collision**: Why proper delimiters/length prefixes are critical
3. **Security Best Practices**: How to prevent seed collision attacks
4. **Real-World Impact**: Why this matters in production Solana programs

## 🔧 Program Functions

### `initialize(organization, employee_id)`
Creates a new staking pool PDA for the given organization/employee combination.

### `stake(amount)`
Stakes SOL into your pool.

### `withdraw(amount)`
Withdraws SOL from your pool (if you have sufficient balance).

## 🎯 Win Condition

Steal at least **50 SOL** from the admin pool to your wallet. The server monitors your balance and will automatically detect when you've won!

## 📚 Real-World Examples

This vulnerability has appeared in production Solana programs:

- **Saber Protocol** (2021): Similar seed collision in LP token minting
- **Mercurial Finance** (2021): PDA collision in vault derivation
- **Best Practice**: Always use length-prefixed seeds or include separators!

## 🛡️ Mitigation

**Vulnerable Code:**
```rust
Pubkey::find_program_address(
    &[b"POOL", org.as_bytes(), emp.as_bytes()],
    program_id,
)
```

**Fixed Code:**
```rust
Pubkey::find_program_address(
    &[
        b"POOL",
        &[org.len() as u8], org.as_bytes(),  // Length prefix
        &[emp.len() as u8], emp.as_bytes(),
    ],
    program_id,
)
```

Or use a delimiter:
```rust
Pubkey::find_program_address(
    &[b"POOL", b":", org.as_bytes(), b":", emp.as_bytes()],
    program_id,
)
```

## 📖 Resources

- [Solana Cookbook - PDAs](https://solanacookbook.com/core-concepts/pdas.html)
- [Anchor Security](https://www.anchor-lang.com/docs/security)
- [Neodyme Security Blog](https://blog.neodyme.io/)

## 🏆 Solution

See [SOLUTION.md](SOLUTION.md) for the complete walkthrough (spoilers!).

---

**Good luck, hacker! 🚀**
